# Parameters
$GPOName = "Edge-Startup-Configuration"
$TargetURL = ""
$DomainName = (Get-ADDomain).DNSRoot

# Check if the Group Policy Management module is available
if (-not (Get-Module -ListAvailable -Name GroupPolicy)) {
    Write-Host "GroupPolicy module not found. Installing RSAT tools..."
    Add-WindowsCapability -Online -Name Rsat.GroupPolicy.Management.Tools~~~~0.0.1.0
}

# Create a new GPO
Write-Host "Creating new GPO: $GPOName"
New-GPO -Name $GPOName -Comment "Configures Microsoft Edge to open specific URL on startup"

# Configure Edge policies
$EdgePolicies = @(
    # Configure startup URL
    @{
        KeyPath = "Software\Policies\Microsoft\Edge"
        ValueName = "RestoreOnStartup"
        ValueData = 4  # Open a list of URLs
        ValueType = "DWord"
    },
    # Set Homepage
    @{
        KeyPath = "Software\Policies\Microsoft\Edge"
        ValueName = "HomepageLocation"
        ValueData = $TargetURL
        ValueType = "String"
    },
    # Disable New Tab Page as Homepage
    @{
        KeyPath = "Software\Policies\Microsoft\Edge"
        ValueName = "HomepageIsNewTabPage"
        ValueData = 0
        ValueType = "DWord"
    },
    # Hide First Run Experience
    @{
        KeyPath = "Software\Policies\Microsoft\Edge"
        ValueName = "HideFirstRunExperience"
        ValueData = 1
        ValueType = "DWord"
    },
    # Disable Welcome Experience
    @{
        KeyPath = "Software\Policies\Microsoft\Edge"
        ValueName = "ShowWelcomeExperience"
        ValueData = 0
        ValueType = "DWord"
    }
)

# Apply the Edge policies
foreach ($policy in $EdgePolicies) {
    Write-Host "Setting policy: $($policy.KeyPath)\$($policy.ValueName)"
    Set-GPRegistryValue -Name $GPOName -Key $policy.KeyPath -ValueName $policy.ValueName -Value $policy.ValueData -Type $policy.ValueType
}

# Create RestoreOnStartupURLs key and add the URL
$StartupURLsKey = "Software\Policies\Microsoft\Edge\RestoreOnStartupURLs"
Write-Host "Creating key: $StartupURLsKey"
# First create the key
Set-GPRegistryValue -Name $GPOName -Key $StartupURLsKey -ValueName "placeholder" -Value "temp" -Type String
# Remove the placeholder value
Remove-GPRegistryValue -Name $GPOName -Key $StartupURLsKey -ValueName "placeholder"
# Add our URL
Set-GPRegistryValue -Name $GPOName -Key $StartupURLsKey -ValueName "1" -Value $TargetURL -Type String

# Link the GPO to the domain
$DomainDN = (Get-ADDomain).DistinguishedName
Write-Host "Linking GPO to domain: $DomainDN"
New-GPLink -Name $GPOName -Target $DomainDN -LinkEnabled Yes