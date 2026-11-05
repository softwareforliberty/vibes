@{
    Run          = @{
        Path     = './tests'
        PassThru = $true
    }
    CodeCoverage = @{
        Enabled               = $true
        Path                  = './src'
        CoveragePercentTarget = 80
    }
}
