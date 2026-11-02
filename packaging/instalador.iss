; Instalador do Alumínio Manager (Inno Setup)
; Compilar: ISCC.exe /DAppVersion=1.6.0 packaging\instalador.iss

#define AppName "Alumínio Manager"
#define AppExe "AluminioManager.exe"
#define AppPublisher "HCsoftware"
#ifndef AppVersion
  #define AppVersion "1.6.0"
#endif

[Setup]
AppId={{A7F3D2C1-5B4E-4F8A-9C2D-1E6B7A8C9D0E}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL=https://condessa.github.io/hcsoftware/
AppSupportURL=https://github.com/condessa/Aluminio-Manager
AppUpdatesURL=https://github.com/condessa/Aluminio-Manager/releases
DefaultDirName={localappdata}\Programs\Aluminio Manager
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=AluminioManager-Setup-{#AppVersion}
SetupIconFile={#SourcePath}\hcsoftware.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
SourceDir=..

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar um atalho no ambiente de trabalho"; GroupDescription: "Atalhos:"

[Files]
Source: "dist\AluminioManager\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"; IconFilename: "{app}\{#AppExe}"
Name: "{group}\Desinstalar o {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; IconFilename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Abrir o {#AppName}"; Flags: nowait postinstall skipifsilent
