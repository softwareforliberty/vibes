%{
  configs: [
    %{
      name: "default",
      checks: %{
        extra: [
          {Credo.Check.Refactor.CyclomaticComplexity, [max_complexity: 10]}
        ]
      }
    }
  ]
}
