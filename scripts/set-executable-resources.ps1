[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string[]]$ExecutablePath,

    [Parameter(Mandatory)]
    [string]$IconPath,

    [string]$ProductName = 'ArHub',
    [string]$FileDescription = 'ArHub - AI Research Hub',
    [string]$CompanyName = '',
    [string]$Copyright = 'ArHub Contributors'
)

$ErrorActionPreference = 'Stop'
$resolvedIcon = (Resolve-Path -LiteralPath $IconPath).Path

if (-not ('ArHubPeResources' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;

public static class ArHubPeResources
{
    private const uint LoadLibraryAsDataFile = 0x00000002;
    private static readonly IntPtr IconResource = new IntPtr(3);
    private static readonly IntPtr GroupIconResource = new IntPtr(14);

    private delegate bool EnumResourceNameCallback(
        IntPtr module,
        IntPtr type,
        IntPtr name,
        IntPtr parameter);

    private delegate bool EnumResourceLanguageCallback(
        IntPtr module,
        IntPtr type,
        IntPtr name,
        ushort language,
        IntPtr parameter);

    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern IntPtr LoadLibraryEx(string fileName, IntPtr file, uint flags);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool FreeLibrary(IntPtr module);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool EnumResourceNames(
        IntPtr module,
        IntPtr type,
        EnumResourceNameCallback callback,
        IntPtr parameter);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool EnumResourceLanguages(
        IntPtr module,
        IntPtr type,
        IntPtr name,
        EnumResourceLanguageCallback callback,
        IntPtr parameter);

    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern IntPtr BeginUpdateResource(
        string fileName,
        bool deleteExistingResources);

    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern bool UpdateResource(
        IntPtr update,
        IntPtr type,
        IntPtr name,
        ushort language,
        byte[] data,
        uint size);

    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern bool UpdateResource(
        IntPtr update,
        IntPtr type,
        IntPtr name,
        ushort language,
        IntPtr data,
        uint size);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool EndUpdateResource(IntPtr update, bool discard);

    private sealed class IconEntry
    {
        public byte Width;
        public byte Height;
        public byte ColorCount;
        public byte Reserved;
        public ushort Planes;
        public ushort BitCount;
        public byte[] Data;
    }

    private static bool IsIntegerResource(IntPtr value)
    {
        return ((ulong)value.ToInt64() >> 16) == 0;
    }

    private static List<ushort> ResourceIds(IntPtr module, IntPtr type)
    {
        var ids = new List<ushort>();
        EnumResourceNameCallback callback = delegate(
            IntPtr unusedModule,
            IntPtr unusedType,
            IntPtr name,
            IntPtr unusedParameter)
        {
            if (IsIntegerResource(name))
            {
                ids.Add((ushort)name.ToInt64());
            }
            return true;
        };

        EnumResourceNames(module, type, callback, IntPtr.Zero);
        return ids.Distinct().OrderBy(value => value).ToList();
    }

    private static List<ushort> ResourceLanguages(IntPtr module, IntPtr type, ushort id)
    {
        var languages = new List<ushort>();
        EnumResourceLanguageCallback callback = delegate(
            IntPtr unusedModule,
            IntPtr unusedType,
            IntPtr unusedName,
            ushort language,
            IntPtr unusedParameter)
        {
            languages.Add(language);
            return true;
        };

        EnumResourceLanguages(module, type, new IntPtr(id), callback, IntPtr.Zero);
        return languages.Distinct().ToList();
    }

    private static List<IconEntry> ReadIcon(string path)
    {
        using (var stream = File.OpenRead(path))
        using (var reader = new BinaryReader(stream))
        {
            if (reader.ReadUInt16() != 0 || reader.ReadUInt16() != 1)
            {
                throw new InvalidDataException("The supplied file is not a Windows icon.");
            }

            int count = reader.ReadUInt16();
            var entries = new List<IconEntry>();
            for (int index = 0; index < count; index++)
            {
                var entry = new IconEntry
                {
                    Width = reader.ReadByte(),
                    Height = reader.ReadByte(),
                    ColorCount = reader.ReadByte(),
                    Reserved = reader.ReadByte(),
                    Planes = reader.ReadUInt16(),
                    BitCount = reader.ReadUInt16()
                };
                uint length = reader.ReadUInt32();
                uint offset = reader.ReadUInt32();
                long nextEntry = stream.Position;
                stream.Position = offset;
                entry.Data = reader.ReadBytes(checked((int)length));
                if (entry.Data.Length != length)
                {
                    throw new EndOfStreamException("The icon contains a truncated image.");
                }
                stream.Position = nextEntry;
                entries.Add(entry);
            }
            return entries;
        }
    }

    private static byte[] BuildGroup(List<IconEntry> entries, List<ushort> ids)
    {
        using (var stream = new MemoryStream())
        using (var writer = new BinaryWriter(stream))
        {
            writer.Write((ushort)0);
            writer.Write((ushort)1);
            writer.Write((ushort)entries.Count);
            for (int index = 0; index < entries.Count; index++)
            {
                IconEntry entry = entries[index];
                writer.Write(entry.Width);
                writer.Write(entry.Height);
                writer.Write(entry.ColorCount);
                writer.Write(entry.Reserved);
                writer.Write(entry.Planes);
                writer.Write(entry.BitCount);
                writer.Write((uint)entry.Data.Length);
                writer.Write(ids[index]);
            }
            return stream.ToArray();
        }
    }

    public static int ReplaceUtf16(string executablePath, string oldValue, string newValue)
    {
        byte[] data = File.ReadAllBytes(executablePath);
        byte[] oldBytes = System.Text.Encoding.Unicode.GetBytes(oldValue + '\0');
        byte[] newBytes = System.Text.Encoding.Unicode.GetBytes(newValue + '\0');
        if (newBytes.Length > oldBytes.Length)
        {
            throw new ArgumentException("A replacement is longer than the existing resource value.");
        }

        int count = 0;
        for (int offset = 0; offset <= data.Length - oldBytes.Length; offset++)
        {
            if (data[offset] != oldBytes[0])
            {
                continue;
            }

            bool match = true;
            for (int index = 1; index < oldBytes.Length; index++)
            {
                if (data[offset + index] != oldBytes[index])
                {
                    match = false;
                    break;
                }
            }
            if (!match)
            {
                continue;
            }

            Array.Clear(data, offset, oldBytes.Length);
            Buffer.BlockCopy(newBytes, 0, data, offset, newBytes.Length);
            count++;
            offset += oldBytes.Length - 1;
        }

        File.WriteAllBytes(executablePath, data);
        return count;
    }

    public static void SetIcon(string executablePath, string iconPath)
    {
        List<IconEntry> entries = ReadIcon(iconPath);
        IntPtr module = LoadLibraryEx(executablePath, IntPtr.Zero, LoadLibraryAsDataFile);
        if (module == IntPtr.Zero)
        {
            throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
        }

        List<ushort> oldIcons;
        List<ushort> oldGroups;
        List<ushort> languages;
        try
        {
            oldIcons = ResourceIds(module, IconResource);
            oldGroups = ResourceIds(module, GroupIconResource);
            ushort groupForLanguage = oldGroups.Count > 0 ? oldGroups[0] : (ushort)1;
            languages = ResourceLanguages(module, GroupIconResource, groupForLanguage);
        }
        finally
        {
            FreeLibrary(module);
        }

        ushort groupId = oldGroups.Count > 0 ? oldGroups[0] : (ushort)1;
        ushort language = languages.Count > 0 ? languages[0] : (ushort)1033;
        ushort nextId = oldIcons.Count > 0 ? (ushort)(oldIcons.Max() + 1) : (ushort)1;
        var iconIds = new List<ushort>();
        for (int index = 0; index < entries.Count; index++)
        {
            iconIds.Add(index < oldIcons.Count ? oldIcons[index] : nextId++);
        }

        IntPtr update = BeginUpdateResource(executablePath, false);
        if (update == IntPtr.Zero)
        {
            throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
        }

        bool success = false;
        try
        {
            for (int index = 0; index < entries.Count; index++)
            {
                byte[] image = entries[index].Data;
                if (!UpdateResource(
                    update,
                    IconResource,
                    new IntPtr(iconIds[index]),
                    language,
                    image,
                    (uint)image.Length))
                {
                    throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
                }
            }

            foreach (ushort id in oldIcons.Where(id => !iconIds.Contains(id)))
            {
                if (!UpdateResource(
                    update,
                    IconResource,
                    new IntPtr(id),
                    language,
                    IntPtr.Zero,
                    0))
                {
                    throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
                }
            }

            byte[] group = BuildGroup(entries, iconIds);
            if (!UpdateResource(
                update,
                GroupIconResource,
                new IntPtr(groupId),
                language,
                group,
                (uint)group.Length))
            {
                throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
            }

            foreach (ushort id in oldGroups.Where(id => id != groupId))
            {
                if (!UpdateResource(
                    update,
                    GroupIconResource,
                    new IntPtr(id),
                    language,
                    IntPtr.Zero,
                    0))
                {
                    throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
                }
            }
            success = true;
        }
        finally
        {
            if (!EndUpdateResource(update, !success) && success)
            {
                throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
            }
        }
    }
}
'@
}

foreach ($path in $ExecutablePath) {
    $resolvedExecutable = (Resolve-Path -LiteralPath $path).Path
    $signature = Get-AuthenticodeSignature -LiteralPath $resolvedExecutable
    if ($signature.Status -ne [System.Management.Automation.SignatureStatus]::NotSigned) {
        throw "Refusing to rewrite a signed executable: $resolvedExecutable ($($signature.Status))"
    }

    $before = (Get-Item -LiteralPath $resolvedExecutable).VersionInfo
    $replacements = @(
        [pscustomobject]@{ Old = $before.FileDescription; New = $FileDescription }
        [pscustomobject]@{ Old = $before.LegalCopyright; New = $Copyright }
        [pscustomobject]@{ Old = $before.ProductName; New = $ProductName }
        [pscustomobject]@{ Old = $before.InternalName; New = $ProductName }
        [pscustomobject]@{ Old = $before.CompanyName; New = $CompanyName }
    )

    $changedValues = 0
    foreach ($replacement in $replacements) {
        if ([string]::IsNullOrEmpty($replacement.Old) -or $replacement.Old -ceq $replacement.New) {
            continue
        }
        $changedValues += [ArHubPeResources]::ReplaceUtf16(
            $resolvedExecutable,
            $replacement.Old,
            $replacement.New
        )
    }

    [ArHubPeResources]::SetIcon($resolvedExecutable, $resolvedIcon)

    $after = (Get-Item -LiteralPath $resolvedExecutable).VersionInfo
    $afterSignature = Get-AuthenticodeSignature -LiteralPath $resolvedExecutable
    [pscustomobject]@{
        Path = $resolvedExecutable
        ProductName = $after.ProductName
        FileDescription = $after.FileDescription
        CompanyName = $after.CompanyName
        InternalName = $after.InternalName
        LegalCopyright = $after.LegalCopyright
        UpdatedValues = $changedValues
        SignatureStatus = $afterSignature.Status
    }
}
