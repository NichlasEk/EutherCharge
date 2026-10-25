// Offline synthetic config decoding only. Run with read-only SDK and no devices/network.
using System;
using System.Reflection;
using System.Collections;

class ConfigDecodeProbe {
    static object Property(object value, string name) {
        return value.GetType().GetProperty(name).GetValue(value, null);
    }
    static void Main(string[] args) {
        if (args.Length != 1) throw new ArgumentException("SDK directory required");
        var assembly = Assembly.LoadFrom(System.IO.Path.Combine(args[0], "Nyquest.Core.dll"));
        var loader = assembly.GetType("Nyquest.Core.MaskRomLoader", true);
        var bodies = (IEnumerable)loader.GetMethod("Load", BindingFlags.Static | BindingFlags.NonPublic | BindingFlags.Public).Invoke(null, null);
        object body = null;
        foreach (var candidate in bodies) {
            if (Property(candidate, "Id").ToString() == "NY8B062D") body = candidate;
        }
        if (body == null) throw new Exception("Missing device profile");
        int words = (int)Property(body, "ConfigSizeInWord");
        if (words != 16) throw new Exception("Unexpected device configuration size");
        Console.WriteLine("size=" + words);
        var converterType = assembly.GetType("Nyquest.Core.NY8ConfigBlockConverter", true);
        var converter = Activator.CreateInstance(converterType, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance, null, new[] {body}, null);
        var config = Activator.CreateInstance(assembly.GetType("Nyquest.Core.NY8ConfigBlockConvertConfig", true));
        int version = (int)Property(config, "ConfigVersion");
        if (version != 3) throw new Exception("Unexpected SDK default configuration version");
        Console.WriteLine("configVersion=" + version);
        var load = converterType.GetMethod("LoadFrom", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        for (int bits = 0; bits < 32; bits++) {
            var bytes = new byte[32];
            bytes[1] = (byte)(bits & 3);
            bytes[12] = (byte)(((bits >> 2) & 3) << 4);
            bytes[17] = (byte)(((bits >> 4) & 1) << 2);
            bool ok = (bool)load.Invoke(converter, new object[] {bytes, 0, config});
            if (!ok) throw new Exception("Manufacturer reader rejected synthetic case " + bits);
            Console.Write(bits + " " + ok);
            foreach (var name in new[] {"Wdt", "WdtEvent", "WdtTimeBase", "ReadIoSource"}) {
                Console.Write(" " + name + "=" + Property(body, name));
            }
            Console.WriteLine();
        }
    }
}
