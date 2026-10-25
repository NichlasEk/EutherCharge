// Offline manufacturer field-layout probe. Supply SDK directory in an isolated runtime.
// Only constructs register metadata/helpers; never opens a ROM or programmer.
using System;using System.Reflection;using System.Runtime.Serialization;
class ConfigProbe {
 static void Main(string[] args){
  if(args.Length!=1)throw new ArgumentException("SDK directory required");
  var a=Assembly.LoadFrom(System.IO.Path.Combine(args[0],"Nyquest.Core.dll"));
  var body=FormatterServices.GetUninitializedObject(a.GetType("Nyquest.Core.NY8MaskRom",true));
  var t=a.GetType("Nyquest.Core.NY8ConfigBlockConverter",true);
  var c=Activator.CreateInstance(t,BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance,null,new object[]{body},null);
  var helper=a.GetType("Nyquest.Core.RegisterHelper",true);var regType=a.GetType("Nyquest.Core.Register",true);
  var get=helper.GetMethod("Get",new[]{regType});int checks=0;
  Console.Write("{\"schema\":1,\"scope\":\"SDK config block offsets, not MCU program addresses\",\"fields\":{");
  bool first=true;
  foreach(var name in new[]{"wdtReg","wdtEventReg","wdtTimeBaseReg","rdPortTypeReg","instClockReg","instructionClockReg"}){
   var reg=t.GetField(name,BindingFlags.NonPublic|BindingFlags.Instance).GetValue(c);
   if(!first)Console.Write(",");first=false;Console.Write("\""+name+"\":[");bool hit=false;
   for(int bit=0;bit<512;bit++){
    var bytes=new byte[64];bytes[bit/8]=(byte)(1<<(bit%8));
    var h=Activator.CreateInstance(helper,new object[]{bytes,0,0,true});
    var value=(uint)get.Invoke(h,new object[]{reg});checks++;
    if(value!=0){if(hit)Console.Write(",");hit=true;Console.Write("{\"byte\":"+(bit/8)+",\"bit\":"+(bit%8)+",\"value\":"+value+"}");}
   }
   Console.Write("]");
  }
  Console.WriteLine("},\"oneHotChecks\":"+checks+"}");
 }
}
