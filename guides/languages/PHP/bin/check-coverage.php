<?php

declare(strict_types=1);

[, $report, $minimum] = $argv;

$metrics = simplexml_load_file($report)->project->metrics;
$total = (int) $metrics['statements'];
$covered = (int) $metrics['coveredstatements'];
$percent = $total === 0 ? 100.0 : 100 * $covered / $total;

if ($percent < (float) $minimum) {
    fwrite(STDERR, sprintf(
        "Line coverage %.1f%% is below %s%%.\n",
        $percent,
        $minimum,
    ));
    exit(1);
}
