; AnchorNote Inno Setup script
; Save as AnchorNoteInstaller.iss and compile with Inno Setup (ISCC.exe).
; Adjust Source paths to reflect where your build artifacts are located.

[Setup]
AppName=Anchor Note
AppVersion=0.1.0
DefaultDirName={autopf}\AnchorNote
DefaultGroupName=Anchor Note
DisableProgramGroupPage=yes
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
OutputBaseFilename=AnchorNote_Installer
CompressionThreads=2

[Files]
; Copy entire dist folder contents for each artifact
; Update these Source patterns to match your local build output
Source: "dist\anchor_note_agent\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\anchor_note_service\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Ensure alert.wav is included (in case it wasn't part of dist)
Source: "anchor_note\assets\alert.wav"; DestDir: "{app}\anchor_note\assets"; Flags: ignoreversion

[Icons]
Name: "{group}\Anchor Note"; Filename: "{app}\anchor_note_agent.exe"; WorkingDir: "{app}"
Name: "{group}\Uninstall Anchor Note"; Filename: "{uninstallexe}"

[Run]
; After install: optionally create the Windows service (runs as SYSTEM)
; sc.exe requires quoting; Inno runs as admin due to PrivilegesRequired=admin
Filename: "sc.exe"; Parameters: "create AnchorNoteService binPath= """"{app}\anchor_note_service.exe"""" DisplayName= ""Anchor Note Service"" start= auto"; Flags: runhidden waituntilterminated
Filename: "sc.exe"; Parameters: "start AnchorNoteService"; Flags: runhidden waituntilterminated

; Create Scheduled Task to run the agent at logon (WakeToRun is configured later via schtasks)
; Note: using schtasks here for better compatibility with arguments/quoting
Filename: "schtasks.exe"; Parameters: "/Create /TN ""AnchorNoteAgent"" /TR ""\""{app}\anchor_note_agent.exe\"""" /SC ONLOGON /RL HIGHEST /F"; Flags: runhidden waituntilterminated

[UninstallRun]
; Stop and remove service on uninstall
Filename: "sc.exe"; Parameters: "stop AnchorNoteService"; Flags: runhidden waituntilterminated
Filename: "sc.exe"; Parameters: "delete AnchorNoteService"; Flags: runhidden waituntilterminated

[Messages]
; Customize messages (optional)
