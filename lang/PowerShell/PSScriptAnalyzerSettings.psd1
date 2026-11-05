@{
    Severity            = @('Error', 'Warning', 'Information')
    IncludeDefaultRules = $true
    Rules               = @{
        PSPlaceOpenBrace                          = @{
            Enable             = $true
            OnSameLine         = $true
            NewLineAfter       = $true
            IgnoreOneLineBlock = $true
        }
        PSPlaceCloseBrace                         = @{
            Enable             = $true
            NewLineAfter       = $false
            IgnoreOneLineBlock = $true
            NoEmptyLineBefore  = $false
        }
        PSUseConsistentIndentation                = @{
            Enable          = $true
            Kind            = 'space'
            IndentationSize = 4
        }
        PSUseConsistentWhitespace                 = @{
            Enable          = $true
            CheckInnerBrace = $true
            CheckOpenBrace  = $true
            CheckOpenParen  = $true
            CheckOperator   = $true
            CheckPipe       = $true
            CheckSeparator  = $true
        }
        PSUseCorrectCasing                        = @{ Enable = $true }
        PSAvoidLongLines                          = @{
            Enable            = $true
            MaximumLineLength = 115
        }
        PSAvoidUsingDoubleQuotesForConstantString = @{ Enable = $true }
        PSAvoidSemicolonsAsLineTerminators        = @{ Enable = $true }
    }
}
