[Setup]
AppName=MyHTS
AppVersion=1.0
DefaultDirName={pf}\MyHTS
DefaultGroupName=MyHTS
OutputDir=installer
OutputBaseFilename=MyHTS_Setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\main.exe"; DestDir: "{app}"

[Icons]
Name: "{group}\MyHTS"; Filename: "{app}\main.exe"
Name: "{commondesktop}\MyHTS"; Filename: "{app}\main.exe"

[Run]
Filename: "{app}\main.exe"; Description: "MyHTS 실행"; Flags: nowait postinstall skipifsilent