#!/bin/bash

# Development Environment Setup Script for Oracle Linux
# This script sets up a complete development environment with:
# - Enhanced terminal experience
# - Tiling window manager
# - Development tools
# - Productivity enhancements
# - Visual improvements

# Set up error handling
set -e
trap 'echo "Error on line $LINENO. Exit code: $?" >&2' ERR

# Function to display section headers
section() {
    echo -e "\n\033[1;32m==>\033[0m \033[1m$1\033[0m"
}

# Function to run commands with status output
run() {
    echo -e "\033[1;34m-->\033[0m $1"
    if eval "$1"; then
        echo -e "\033[1;32m-->\033[0m Done"
    else
        echo -e "\033[1;31m-->\033[0m Failed"
        return 1
    fi
}

# Update system packages
section "Updating system packages"
run "sudo dnf update -y"

# Install essential repositories
section "Setting up additional repositories"
run "sudo dnf install -y epel-release"
run "sudo dnf config-manager --set-enabled ol8_developer_EPEL"
run "sudo dnf config-manager --set-enabled ol8_codeready_builder"

# Install development tools
section "Installing development tools"
run "sudo dnf groupinstall -y 'Development Tools'"
run "sudo dnf install -y git curl wget vim neovim nodejs npm python3 python3-pip"

# Install Docker
section "Installing Docker"
run "sudo dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo"
run "sudo dnf install -y docker-ce docker-ce-cli containerd.io"
run "sudo systemctl enable --now docker"
run "sudo usermod -aG docker $USER"

# Install a better terminal (using xterm instead of GPU-accelerated Alacritty for VM compatibility)
section "Installing an enhanced terminal"
run "sudo dnf install -y xterm"

# Install ZSH and Oh My Zsh
section "Setting up ZSH with Oh My Zsh"
run "sudo dnf install -y zsh"
run "sh -c \"\$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)\" \"\" --unattended"
run "chsh -s \$(which zsh)"

# Install and configure Tmux
section "Setting up Tmux terminal multiplexer"
run "sudo dnf install -y tmux"
cat > ~/.tmux.conf << 'EOL'
# Enable mouse mode
set -g mouse on

# Start window numbering at 1
set -g base-index 1

# Set prefix to Ctrl+a
unbind C-b
set-option -g prefix C-a
bind-key C-a send-prefix

# Split panes using | and -
bind | split-window -h
bind - split-window -v
unbind '"'
unbind %

# Reload config file
bind r source-file ~/.tmux.conf \; display "Config reloaded!"

# Switch panes using Alt-arrow without prefix
bind -n M-Left select-pane -L
bind -n M-Right select-pane -R
bind -n M-Up select-pane -U
bind -n M-Down select-pane -D

# Enable 256 colors
set -g default-terminal "screen-256color"

# Set status bar
set -g status-bg black
set -g status-fg white
EOL

# Install Fluxbox window manager
section "Installing Fluxbox window manager"
run "sudo dnf install -y fluxbox"

# Using i3status (skipped as requested)
section "Skipping i3status installation as requested"

# Install Rofi application launcher
section "Installing Rofi application launcher"
run "sudo dnf install -y rofi"

# Install better fonts
section "Installing improved fonts"
run "sudo dnf install -y fontconfig"
mkdir -p ~/.local/share/fonts
run "wget -O ~/.local/share/fonts/FiraCode.zip https://github.com/ryanoasis/nerd-fonts/releases/download/v2.1.0/FiraCode.zip"
run "unzip ~/.local/share/fonts/FiraCode.zip -d ~/.local/share/fonts/"
run "fc-cache -fv"

# Install productivity tools
section "Installing productivity tools"
run "sudo dnf install -y fzf ripgrep fd-find bat"

# Install and configure Neovim (skipped as requested)
section "Skipping Neovim installation as requested"

# Configure i3
section "Configuring i3 window manager"
mkdir -p ~/.config/i3
cat > ~/.config/i3/config << 'EOL'
# i3 config file (v4)

# Set mod key (Mod1=<Alt>, Mod4=<Super>)
set $mod Mod4

# Set default font
font pango:monospace 10

# Use Mouse+$mod to drag floating windows
floating_modifier $mod

# Start a terminal
bindsym $mod+Return exec xterm

# Kill focused window
bindsym $mod+Shift+q kill

# Start rofi (program launcher)
bindsym $mod+d exec --no-startup-id rofi -show drun

# Change focus
bindsym $mod+j focus left
bindsym $mod+k focus down
bindsym $mod+l focus up
bindsym $mod+semicolon focus right

# Alternatively, use cursor keys
bindsym $mod+Left focus left
bindsym $mod+Down focus down
bindsym $mod+Up focus up
bindsym $mod+Right focus right

# Move focused window
bindsym $mod+Shift+j move left
bindsym $mod+Shift+k move down
bindsym $mod+Shift+l move up
bindsym $mod+Shift+semicolon move right

# Alternatively, use cursor keys to move windows
bindsym $mod+Shift+Left move left
bindsym $mod+Shift+Down move down
bindsym $mod+Shift+Up move up
bindsym $mod+Shift+Right move right

# Split in horizontal orientation
bindsym $mod+h split h

# Split in vertical orientation
bindsym $mod+v split v

# Enter fullscreen mode for the focused container
bindsym $mod+f fullscreen toggle

# Change container layout (stacked, tabbed, toggle split)
bindsym $mod+s layout stacking
bindsym $mod+w layout tabbed
bindsym $mod+e layout toggle split

# Toggle tiling / floating
bindsym $mod+Shift+space floating toggle

# Change focus between tiling / floating windows
bindsym $mod+space focus mode_toggle

# Focus the parent container
bindsym $mod+a focus parent

# Define names for default workspaces
set $ws1 "1: Terminal"
set $ws2 "2: Code"
set $ws3 "3: Web"
set $ws4 "4: Docs"
set $ws5 "5: Chat"
set $ws6 "6: Media"
set $ws7 "7"
set $ws8 "8"
set $ws9 "9"
set $ws10 "10"

# Switch to workspace
bindsym $mod+1 workspace $ws1
bindsym $mod+2 workspace $ws2
bindsym $mod+3 workspace $ws3
bindsym $mod+4 workspace $ws4
bindsym $mod+5 workspace $ws5
bindsym $mod+6 workspace $ws6
bindsym $mod+7 workspace $ws7
bindsym $mod+8 workspace $ws8
bindsym $mod+9 workspace $ws9
bindsym $mod+0 workspace $ws10

# Move focused container to workspace
bindsym $mod+Shift+1 move container to workspace $ws1
bindsym $mod+Shift+2 move container to workspace $ws2
bindsym $mod+Shift+3 move container to workspace $ws3
bindsym $mod+Shift+4 move container to workspace $ws4
bindsym $mod+Shift+5 move container to workspace $ws5
bindsym $mod+Shift+6 move container to workspace $ws6
bindsym $mod+Shift+7 move container to workspace $ws7
bindsym $mod+Shift+8 move container to workspace $ws8
bindsym $mod+Shift+9 move container to workspace $ws9
bindsym $mod+Shift+0 move container to workspace $ws10

# Reload the configuration file
bindsym $mod+Shift+c reload

# Restart i3 inplace
bindsym $mod+Shift+r restart

# Exit i3
bindsym $mod+Shift+e exec "i3-nagbar -t warning -m 'Do you really want to exit i3?' -b 'Yes, exit i3' 'i3-msg exit'"

# Resize window
mode "resize" {
        bindsym j resize shrink width 10 px or 10 ppt
        bindsym k resize grow height 10 px or 10 ppt
        bindsym l resize shrink height 10 px or 10 ppt
        bindsym semicolon resize grow width 10 px or 10 ppt
        
        bindsym Left resize shrink width 10 px or 10 ppt
        bindsym Down resize grow height 10 px or 10 ppt
        bindsym Up resize shrink height 10 px or 10 ppt
        bindsym Right resize grow width 10 px or 10 ppt
        
        bindsym Return mode "default"
        bindsym Escape mode "default"
        bindsym $mod+r mode "default"
}

bindsym $mod+r mode "resize"

# Use lightweight i3status instead of polybar for better VM performance
bar {
    status_command i3status
    position top
    colors {
        background #282A36
        statusline #F8F8F2
        separator  #44475A

        focused_workspace  #44475A #44475A #F8F8F2
        active_workspace   #282A36 #44475A #F8F8F2
        inactive_workspace #282A36 #282A36 #BFBFBF
        urgent_workspace   #FF5555 #FF5555 #F8F8F2
        binding_mode       #FF5555 #FF5555 #F8F8F2
    }
}

# Polybar disabled for VM compatibility
# exec_always --no-startup-id $HOME/.config/polybar/launch.sh

# Set wallpaper
exec_always --no-startup-id feh --bg-fill $HOME/Pictures/wallpaper.jpg

# Compositor disabled for VM compatibility
# exec --no-startup-id picom -b

# Appearance
# class                 border  backgr. text    indicator child_border
client.focused          #4c7899 #285577 #ffffff #2e9ef4   #285577
client.focused_inactive #333333 #5f676a #ffffff #484e50   #5f676a
client.unfocused        #333333 #222222 #888888 #292d2e   #222222
client.urgent           #2f343a #900000 #ffffff #900000   #900000
client.placeholder      #000000 #0c0c0c #ffffff #000000   #0c0c0c

# Minimal gaps for better VM performance
gaps inner 2
gaps outer 0

# Remove window borders
for_window [class="^.*"] border pixel 2

# Applications with specific workspaces
assign [class="XTerm"] $ws1
assign [class="Code"] $ws2
assign [class="Firefox"] $ws3
EOL

# Configure Polybar
section "Configuring Polybar"
mkdir -p ~/.config/polybar
cat > ~/.config/polybar/config << 'EOL'
[colors]
background = #222
background-alt = #444
foreground = #dfdfdf
foreground-alt = #888
primary = #ffb52a
secondary = #e60053
alert = #bd2c40

[bar/main]
width = 100%
height = 27
radius = 6.0
fixed-center = false

background = ${colors.background}
foreground = ${colors.foreground}

line-size = 3
line-color = #f00

border-size = 4
border-color = #00000000

padding-left = 0
padding-right = 2

module-margin-left = 1
module-margin-right = 2

font-0 = fixed:pixelsize=10;1
font-1 = unifont:fontformat=truetype:size=8:antialias=false;0
font-2 = "Fira Code Nerd Font:size=10;1"

modules-left = i3
modules-center = date
modules-right = filesystem memory cpu

tray-position = right
tray-padding = 2
tray-background = ${colors.background-alt}

cursor-click = pointer
cursor-scroll = ns-resize

[module/filesystem]
type = internal/fs
interval = 25

mount-0 = /

label-mounted = %{F#0a81f5}%mountpoint%%{F-}: %percentage_used%%
label-unmounted = %mountpoint% not mounted
label-unmounted-foreground = ${colors.foreground-alt}

[module/i3]
type = internal/i3
format = <label-state> <label-mode>
index-sort = true
wrapping-scroll = false

label-mode-padding = 2
label-mode-foreground = #000
label-mode-background = ${colors.primary}

label-focused = %index%
label-focused-background = ${colors.background-alt}
label-focused-underline= ${colors.primary}
label-focused-padding = 2

label-unfocused = %index%
label-unfocused-padding = 2

label-visible = %index%
label-visible-background = ${self.label-focused-background}
label-visible-underline = ${self.label-focused-underline}
label-visible-padding = ${self.label-focused-padding}

label-urgent = %index%
label-urgent-background = ${colors.alert}
label-urgent-padding = 2

[module/cpu]
type = internal/cpu
interval = 2
format-prefix = " "
format-prefix-foreground = ${colors.foreground-alt}
format-underline = #f90000
label = %percentage:2%%

[module/memory]
type = internal/memory
interval = 2
format-prefix = " "
format-prefix-foreground = ${colors.foreground-alt}
format-underline = #4bffdc
label = %percentage_used%%

[module/date]
type = internal/date
interval = 5

date = " %Y-%m-%d"
date-alt = " %Y-%m-%d"

time = %H:%M
time-alt = %H:%M:%S

format-prefix = 
format-prefix-foreground = ${colors.foreground-alt}
format-underline = #0a6cf5

label = %date% %time%

[settings]
screenchange-reload = true

[global/wm]
margin-top = 5
margin-bottom = 5
EOL

# Create Polybar launch script
cat > ~/.config/polybar/launch.sh << 'EOL'
#!/bin/bash

# Terminate already running bar instances
killall -q polybar

# Wait until the processes have been shut down
while pgrep -u $UID -x polybar >/dev/null; do sleep 1; done

# Launch Polybar
polybar main &

echo "Polybar launched..."
EOL
chmod +x ~/.config/polybar/launch.sh

# Configure Alacritty
section "Configuring Alacritty terminal"
mkdir -p ~/.config/alacritty
cat > ~/.config/alacritty/alacritty.yml << 'EOL'
window:
  padding:
    x: 10
    y: 10
  decorations: full
  opacity: 0.95

scrolling:
  history: 10000
  multiplier: 3

font:
  normal:
    family: "FiraCode Nerd Font"
    style: Regular
  bold:
    family: "FiraCode Nerd Font"
    style: Bold
  italic:
    family: "FiraCode Nerd Font"
    style: Italic
  size: 11.0

# Colors (Dracula)
colors:
  primary:
    background: '#282a36'
    foreground: '#f8f8f2'
  cursor:
    text: CellBackground
    cursor: CellForeground
  vi_mode_cursor:
    text: CellBackground
    cursor: CellForeground
  search:
    matches:
      foreground: '#44475a'
      background: '#50fa7b'
    focused_match:
      foreground: '#44475a'
      background: '#ffb86c'
  footer_bar:
    background: '#282a36'
    foreground: '#f8f8f2'
  hints:
    start:
      foreground: '#282a36'
      background: '#f1fa8c'
    end:
      foreground: '#f1fa8c'
      background: '#282a36'
  line_indicator:
    foreground: None
    background: None
  selection:
    text: CellForeground
    background: '#44475a'
  normal:
    black: '#21222c'
    red: '#ff5555'
    green: '#50fa7b'
    yellow: '#f1fa8c'
    blue: '#bd93f9'
    magenta: '#ff79c6'
    cyan: '#8be9fd'
    white: '#f8f8f2'
  bright:
    black: '#6272a4'
    red: '#ff6e6e'
    green: '#69ff94'
    yellow: '#ffffa5'
    blue: '#d6acff'
    magenta: '#ff92df'
    cyan: '#a4ffff'
    white: '#ffffff'

bell:
  animation: EaseOutExpo
  duration: 0

mouse:
  hide_when_typing: true

key_bindings:
  - { key: V, mods: Control|Shift, action: Paste }
  - { key: C, mods: Control|Shift, action: Copy }
  - { key: Insert, mods: Shift, action: PasteSelection }
  - { key: Key0, mods: Control, action: ResetFontSize }
  - { key: Equals, mods: Control, action: IncreaseFontSize }
  - { key: Plus, mods: Control, action: IncreaseFontSize }
  - { key: Minus, mods: Control, action: DecreaseFontSize }
  - { key: F11, mods: None, action: ToggleFullscreen }
  - { key: Paste, mods: None, action: Paste }
  - { key: Copy, mods: None, action: Copy }
  - { key: L, mods: Control, action: ClearLogNotice }
  - { key: L, mods: Control, chars: "\x0c" }
  - { key: PageUp, mods: None, action: ScrollPageUp, mode: ~Alt }
  - { key: PageDown, mods: None, action: ScrollPageDown, mode: ~Alt }
  - { key: Home, mods: Shift, action: ScrollToTop, mode: ~Alt }
  - { key: End, mods: Shift, action: ScrollToBottom, mode: ~Alt }
EOL

# Configure Rofi
section "Configuring Rofi application launcher"
mkdir -p ~/.config/rofi
cat > ~/.config/rofi/config.rasi << 'EOL'
configuration {
    modi: "window,run,ssh,drun";
    width: 50;
    lines: 15;
    columns: 1;
    font: "FiraCode Nerd Font 12";
    bw: 1;
    location: 0;
    padding: 5;
    yoffset: 0;
    xoffset: 0;
    fixed-num-lines: true;
    show-icons: true;
    terminal: "xterm";
    ssh-client: "ssh";
    ssh-command: "{terminal} -e {ssh-client} {host} [-p {port}]";
    run-command: "{cmd}";
    run-list-command: "";
    run-shell-command: "{terminal} -e {cmd}";
    window-command: "wmctrl -i -R {window}";
    window-match-fields: "all";
    icon-theme: "Papirus";
    drun-match-fields: "name,generic,exec,categories,keywords";
    drun-show-actions: false;
    drun-display-format: "{name} [<span weight='light' size='small'><i>({generic})</i></span>]";
    disable-history: false;
    ignored-prefixes: "";
    sort: false;
    sorting-method: "normal";
    case-sensitive: false;
    cycle: true;
    sidebar-mode: false;
    eh: 1;
    auto-select: false;
    parse-hosts: false;
    parse-known-hosts: true;
    combi-modi: "window,run";
    matching: "normal";
    tokenize: true;
    m: "-5";
    line-margin: 2;
    line-padding: 1;
    filter: "";
    separator-style: "dash";
    hide-scrollbar: false;
    fullscreen: false;
    fake-transparency: false;
    dpi: -1;
    threads: 0;
    scrollbar-width: 8;
    scroll-method: 0;
    fake-background: "screenshot";
    window-format: "{w}    {c}   {t}";
    click-to-exit: true;
    show-match: true;
    theme: "dracula";
    max-history-size: 25;
    combi-hide-mode-prefix: false;
    matching-negate-char: '-' /* unsupported */;
    cache-dir: ;
    window-thumbnail: false;
    drun-use-desktop-cache: false;
    drun-reload-desktop-cache: false;
    normalize-match: false;
    pid: "/run/user/1000/rofi.pid";
    display-window: "Windows";
    display-windowcd: "Window CD";
    display-run: "Run";
    display-ssh: "SSH";
    display-drun: "Applications";
    display-combi: "Combi";
    display-keys: "Keys";
    kb-primary-paste: "Control+V,Shift+Insert";
    kb-secondary-paste: "Control+v,Insert";
    kb-clear-line: "Control+w";
    kb-move-front: "Control+a";
    kb-move-end: "Control+e";
    kb-move-word-back: "Alt+b,Control+Left";
    kb-move-word-forward: "Alt+f,Control+Right";
    kb-move-char-back: "Left,Control+b";
    kb-move-char-forward: "Right,Control+f";
    kb-remove-word-back: "Control+Alt+h,Control+BackSpace";
    kb-remove-word-forward: "Control+Alt+d";
    kb-remove-char-forward: "Delete,Control+d";
    kb-remove-char-back: "BackSpace,Shift+BackSpace,Control+h";
    kb-remove-to-eol: "Control+k";
    kb-remove-to-sol: "Control+u";
    kb-accept-entry: "Control+j,Control+m,Return,KP_Enter";
    kb-accept-custom: "Control+Return";
    kb-accept-alt: "Shift+Return";
    kb-delete-entry: "Shift+Delete";
    kb-mode-next: "Shift+Right,Control+Tab";
    kb-mode-previous: "Shift+Left,Control+ISO_Left_Tab";
    kb-row-left: "Control+Page_Up";
    kb-row-right: "Control+Page_Down";
    kb-row-up: "Up,Control+p,ISO_Left_Tab";
    kb-row-down: "Down,Control+n";
    kb-row-tab: "Tab";
    kb-page-prev: "Page_Up";
    kb-page-next: "Page_Down";
    kb-row-first: "Home,KP_Home";
    kb-row-last: "End,KP_End";
    kb-row-select: "Control+space";
    kb-screenshot: "Alt+S";
    kb-ellipsize: "Alt+period";
    kb-toggle-case-sensitivity: "grave,dead_grave";
    kb-toggle-sort: "Alt+grave";
    kb-cancel: "Escape,Control+g,Control+bracketleft";
    kb-custom-1: "Alt+1";
    kb-custom-2: "Alt+2";
    kb-custom-3: "Alt+3";
    kb-custom-4: "Alt+4";
    kb-custom-5: "Alt+5";
    kb-custom-6: "Alt+6";
    kb-custom-7: "Alt+7";
    kb-custom-8: "Alt+8";
    kb-custom-9: "Alt+9";
    kb-custom-10: "Alt+0";
    kb-custom-11: "Alt+exclam";
    kb-custom-12: "Alt+at";
    kb-custom-13: "Alt+numbersign";
    kb-custom-14: "Alt+dollar";
    kb-custom-15: "Alt+percent";
    kb-custom-16: "Alt+dead_circumflex";
    kb-custom-17: "Alt+ampersand";
    kb-custom-18: "Alt+asterisk";
    kb-custom-19: "Alt+parenleft";
    kb-select-1: "Super+1";
    kb-select-2: "Super+2";
    kb-select-3: "Super+3";
    kb-select-4: "Super+4";
    kb-select-5: "Super+5";
    kb-select-6: "Super+6";
    kb-select-7: "Super+7";
    kb-select-8: "Super+8";
    kb-select-9: "Super+9";
    kb-select-10: "Super+0";
    ml-row-left: "ScrollLeft";
    ml-row-right: "ScrollRight";
    ml-row-up: "ScrollUp";
    ml-row-down: "ScrollDown";
    me-select-entry: "MousePrimary";
    me-accept-entry: "MouseDPrimary";
    me-accept-custom: "Control+MouseDPrimary";
}

@theme "dracula"
EOL

# Create a dracula theme for Rofi
cat > ~/.config/rofi/dracula.rasi << 'EOL'
* {
    /* Dracula theme color palette */
    drac-bgd: #282a36;
    drac-cur: #44475a;
    drac-fgd: #f8f8f2;
    drac-cmt: #6272a4;
    drac-cya: #8be9fd;
    drac-grn: #50fa7b;
    drac-ora: #ffb86c;
    drac-pnk: #ff79c6;
    drac-pur: #bd93f9;
    drac-red: #ff5555;
    drac-yel: #f1fa8c;

    /* For dark theme */
    bg0:     @drac-bgd;
    bg1:     @drac-cur;
    fg0:     @drac-fgd;
    fg1:     @drac-cmt;

    /* For accent */
    accent-color:     @drac-pnk;
    urgent-color:     @drac-red;

    background-color: @bg0;
    text-color:       @fg0;

    margin:  0;
    padding: 0;
    spacing: 0;
}

window {
    width:      50%;
    border:     1;
    text-color: @fg0;
    background-color: @bg0;
    border-color:     @accent-color;
    border-radius:    6px;
    padding:    10px;
}

inputbar {
    spacing:    8px; 
    padding:    8px;
    text-color: @fg0;
    background-color: @bg1;
    border-radius:    6px;
}

prompt, entry, element-icon, element-text {
    vertical-align: 0.5;
}

prompt {
    text-color: @accent-color;
}

textbox {
    padding:            8px;
    background-color:   @bg1;
    text-color:         @fg0;
    border-radius:      6px;
}

listview {
    padding:    4px 0;
    lines:      8;
    columns:    1;
    fixed-height:   false;
}

element {
    padding:    8px;
    spacing:    8px;
    border-radius:  6px;
}

element normal normal {
    text-color: @fg0;
    background-color: transparent;
}

element normal urgent {
    text-color: @urgent-color;
}

element normal active {
    text-color: @accent-color;
}

element selected {
    text-color: @bg0;
}

element selected normal, element selected active {
    background-color:   @accent-color;
}

element selected urgent {
    background-color:   @urgent-color;
}

element-icon {
    size:   0.8em;
}

element-text {
    text-color: inherit;
}
EOL

# Note: Skipping compositor installation as it's not suitable for VM environments without GPU
section "Skipping compositor for VM compatibility"
echo "Skipping compositor installation as it may cause performance issues in VM environments"

# Remove wallpaper setup - not needed
section "Skipping wallpaper setup as requested"

# Create Zsh configuration
section "Configuring Zsh"
cat > ~/.zshrc << 'EOL'
# Path to your oh-my-zsh installation.
export ZSH=$HOME/.oh-my-zsh

# Set name of the theme to load
ZSH_THEME="agnoster"

# Which plugins would you like to load?
plugins=(
  git
  docker
  colored-man-pages
  zsh-autosuggestions
  zsh-syntax-highlighting
  z
)

source $ZSH/oh-my-zsh.sh

# User configuration

# Set personal aliases
alias zshconfig="$EDITOR ~/.zshrc"
alias i3config="$EDITOR ~/.config/i3/config"
alias ls="ls --color=auto"
alias ll="ls -la"
alias vim="nvim"
alias g="git"
alias d="docker"
alias dc="docker-compose"
alias k="kubectl"

# Install zsh plugins
if [ ! -d ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions ]; then
  git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
fi

if [ ! -d ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting ]; then
  git clone https://github.com/zsh-users/zsh-syntax-highlighting ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
fi

# Configure fzf if installed
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

# Add local bin to PATH
export PATH=$HOME/.local/bin:$PATH

# NVM configuration
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# Set default editor
export EDITOR='nvim'
export VISUAL='nvim'

# Better history
export HISTSIZE=10000
export SAVEHIST=10000
export HISTFILE=~/.zsh_history
setopt HIST_IGNORE_ALL_DUPS
setopt HIST_SAVE_NO_DUPS
setopt HIST_IGNORE_DUPS
setopt HIST_IGNORE_SPACE
setopt HIST_FIND_NO_DUPS
setopt HIST_REDUCE_BLANKS
setopt INC_APPEND_HISTORY

# Enable color support in less
export LESS_TERMCAP_mb=$'\E[1;31m'     # begin bold
export LESS_TERMCAP_md=$'\E[1;36m'     # begin blink
export LESS_TERMCAP_me=$'\E[0m'        # reset bold/blink
export LESS_TERMCAP_so=$'\E[01;44;33m' # begin reverse video
export LESS_TERMCAP_se=$'\E[0m'        # reset reverse video
export LESS_TERMCAP_us=$'\E[1;32m'     # begin underline
export LESS_TERMCAP_ue=$'\E[0m'        # reset underline
export LESS="-R"

# Function to set terminal title
function set-title() {
  echo -ne "\033]0;${1}\007"
}
EOL

# Install zsh plugins
section "Installing Zsh plugins"
run "git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions"
run "git clone https://github.com/zsh-users/zsh-syntax-highlighting ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting"

# Install Node Version Manager
section "Installing Node Version Manager"
run "curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash"

# Install Python tools
section "Installing Python development tools"
run "pip3 install --user virtualenv pipenv pylint black flake8 jupyter"

# Install Git extensions
section "Installing Git tools"
run "pip3 install --user git-fame"
run "sudo dnf install -y git-extras"

# Install lazygit
section "Installing lazygit"
run "sudo dnf copr enable atim/lazygit -y"
run "sudo dnf install -y lazygit"

# Install default .gitconfig
cat > ~/.gitconfig << 'EOL'
[user]
    name = Your Name
    email = your.email@example.com

[core]
    editor = nvim
    whitespace = fix,-indent-with-non-tab,trailing-space,cr-at-eol
    excludesfile = ~/.gitignore

[color]
    ui = auto

[color "branch"]
    current = yellow bold
    local = green bold
    remote = cyan bold

[color "diff"]
    meta = yellow bold
    frag = magenta bold
    old = red bold
    new = green bold
    whitespace = red reverse

[color "status"]
    added = green bold
    changed = yellow bold
    untracked = red bold

[diff]
    tool = vimdiff

[difftool]
    prompt = false

[alias]
    a = add
    aa = add --all
    c = commit
    cm = commit -m
    ca = commit --amend
    co = checkout
    cb = checkout -b
    d = diff
    ds = diff --staged
    l = log --oneline
    lg = log --oneline --graph --decorate
    ls = ls-files
    s = status -s
    b = branch
    p = push
    pl = pull
EOL

# Configure VS Code (skipped as it's already configured)
section "Skipping VS Code configuration as it's already set up"

# Install common programming language support
section "Installing common programming language support"
run "sudo dnf install -y golang rust java-11-openjdk-devel"
run "sudo dnf install -y python3-devel"

# Add RDP-specific configuration
section "Adding RDP-specific configurations"

# Create ~/.xinitrc for X session startup
cat > ~/.xinitrc << 'EOL'
#!/bin/bash

# Load Xresources
if [ -f ~/.Xresources ]; then
    xrdb -merge ~/.Xresources
fi

# Fix RDP issues
xset -dpms
xset s off

# Set a reasonable DPI for RDP
xrandr --dpi 96

# Start fluxbox
exec fluxbox
EOL
chmod +x ~/.xinitrc

# Create desktop entries
mkdir -p ~/.local/share/applications ~/.local/share/xsessions

# Create desktop entry for xterm with better colors
cat > ~/.local/share/applications/xterm-custom.desktop << 'EOL'
[Desktop Entry]
Name=XTerm (Custom)
Comment=Terminal with Dracula theme
Exec=xterm -fa "FiraCode Nerd Font" -fs 11 -bg "#282a36" -fg "#f8f8f2" -xrm "XTerm*selectToClipboard: true"
Icon=utilities-terminal
Type=Application
Categories=System;TerminalEmulator;
StartupNotify=true
Keywords=shell;prompt;command;commandline;
EOL

# Create xsession entry for fluxbox
cat > ~/.local/share/xsessions/dev-env-fluxbox.desktop << 'EOL'
[Desktop Entry]
Name=Development Environment (Fluxbox)
Comment=Custom development environment with Fluxbox
Exec=~/.xinitrc
Type=Application
EOL

# Display final message
section "Setup Complete!"
echo "Your developer environment has been set up successfully."
echo "This setup has been optimized for VM usage over RDP with the following changes:"
echo " - Using XTerm instead of Alacritty (no GPU dependency)"
echo " - Disabled compositor effects"
echo " - Simplified i3 configuration"
echo " - Added RDP-specific optimizations"
echo " - Using lightweight i3status bar instead of Polybar"
echo ""
echo "Please log out and log back in to start using your new development environment."
echo "When logging back in, select 'i3 (RDP Compatible)' as your desktop environment from the login screen."
echo ""
echo "Some useful keyboard shortcuts for i3:"
echo " - Super+Enter: Open terminal"
echo " - Super+d: Application launcher"
echo " - Super+Shift+q: Close window"
echo " - Super+1-9: Switch workspaces"
echo " - Super+Shift+r: Reload i3 config"
echo " - Super+r: Resize mode"
echo ""
echo "If you experience any display issues:"
echo " 1. Try running 'xrandr --dpi 96' to fix scaling"
echo " 2. Use 'i3-msg restart' to reload the window manager"
echo ""
echo "Enjoy your new development environment!"