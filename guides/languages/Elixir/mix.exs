# Template: merge these settings into your project's mix.exs.
defmodule MyApp.MixProject do
  use Mix.Project

  def project do
    [
      app: :my_app,
      version: "0.1.0",
      elixir: "~> 1.17",
      deps: deps(),
      dialyzer: [
        flags: [:error_handling, :extra_return, :missing_return, :unknown, :unmatched_returns]
      ],
      test_coverage: [summary: [threshold: 80]]
    ]
  end

  defp deps do
    [
      {:credo, "~> 1.7", only: [:dev, :test], runtime: false},
      {:dialyxir, "~> 1.4", only: [:dev, :test], runtime: false},
      {:mix_audit, "~> 2.1", only: [:dev, :test], runtime: false}
    ]
  end
end
