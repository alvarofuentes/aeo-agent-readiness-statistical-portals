param(
    [Parameter(Mandatory = $true)][string]$MarkdownPath,
    [Parameter(Mandatory = $true)][string]$DocxPath,
    [Parameter(Mandatory = $true)][string]$PdfPath
)

$ErrorActionPreference = 'Stop'

function Get-RgbLong([int]$Red, [int]$Green, [int]$Blue) {
    return $Red + (256 * $Green) + (65536 * $Blue)
}

function Clean-Markdown([string]$Text) {
    $clean = $Text
    $clean = [regex]::Replace($clean, '\[([^\]]+)\]\((https?://[^\)]+)\)', '$1 ($2)')
    $clean = [regex]::Replace($clean, '<(https?://[^>]+)>', '$1')
    $clean = $clean.Replace('**', '').Replace('`', '')
    return $clean.Trim()
}

function Add-ParagraphText($Document, [string]$Text, [double]$After = 6, [double]$Before = 0) {
    $paragraph = $Document.Paragraphs.Add()
    $paragraph.Range.Text = (Clean-Markdown $Text)
    $paragraph.Range.Font.Name = 'Calibri'
    $paragraph.Range.Font.Size = 11
    $paragraph.Range.Font.Color = Get-RgbLong 0 0 0
    $paragraph.Format.SpaceBefore = $Before
    $paragraph.Format.SpaceAfter = $After
    $paragraph.Format.LineSpacingRule = 5
    $paragraph.Format.LineSpacing = 12.1
    $paragraph.Format.WidowControl = -1
    return $paragraph
}

function Add-HeadingText($Document, [string]$Text, [int]$Level) {
    $paragraph = $Document.Paragraphs.Add()
    $paragraph.Range.Text = (Clean-Markdown $Text)
    if ($Level -eq 1) {
        $paragraph.Range.Style = -2
        $paragraph.Range.Font.Size = 16
        $paragraph.Format.SpaceBefore = 16
        $paragraph.Format.SpaceAfter = 8
    }
    elseif ($Level -eq 2) {
        $paragraph.Range.Style = -3
        $paragraph.Range.Font.Size = 13
        $paragraph.Format.SpaceBefore = 12
        $paragraph.Format.SpaceAfter = 6
    }
    else {
        $paragraph.Range.Style = -4
        $paragraph.Range.Font.Size = 12
        $paragraph.Format.SpaceBefore = 8
        $paragraph.Format.SpaceAfter = 4
    }
    $paragraph.Range.Font.Name = 'Calibri'
    $paragraph.Range.Font.Bold = -1
    $paragraph.Range.Font.Color = if ($Level -eq 3) { Get-RgbLong 31 77 120 } else { Get-RgbLong 46 116 181 }
    $paragraph.Format.KeepWithNext = -1
    $paragraph.Format.WidowControl = -1
    return $paragraph
}

function Add-ListItem($Document, [string]$Text, [bool]$Numbered) {
    $paragraph = $Document.Paragraphs.Add()
    $paragraph.Range.Text = (Clean-Markdown $Text)
    $paragraph.Range.Font.Name = 'Calibri'
    $paragraph.Range.Font.Size = 11
    if ($Numbered) {
        $paragraph.Range.ListFormat.ApplyNumberDefault()
    }
    else {
        $paragraph.Range.ListFormat.ApplyBulletDefault()
    }
    $paragraph.Format.LeftIndent = 36
    $paragraph.Format.FirstLineIndent = -18
    $paragraph.Format.SpaceAfter = 8
    $paragraph.Format.LineSpacingRule = 5
    $paragraph.Format.LineSpacing = 12.83
    $paragraph.Format.WidowControl = -1
    return $paragraph
}

function Add-CodeBlock($Document, [string[]]$CodeLines) {
    $paragraph = $Document.Paragraphs.Add()
    $paragraph.Range.Text = ($CodeLines -join "`r")
    $paragraph.Range.Font.Name = 'Consolas'
    $paragraph.Range.Font.Size = 9
    $paragraph.Range.Shading.BackgroundPatternColor = Get-RgbLong 242 244 247
    $paragraph.Format.LeftIndent = 12
    $paragraph.Format.RightIndent = 12
    $paragraph.Format.SpaceBefore = 4
    $paragraph.Format.SpaceAfter = 8
    $paragraph.Format.LineSpacingRule = 0
    return $paragraph
}

function Add-Callout($Document, [string]$Text) {
    $paragraph = $Document.Paragraphs.Add()
    $paragraph.Range.Text = (Clean-Markdown $Text)
    $paragraph.Range.Font.Name = 'Calibri'
    $paragraph.Range.Font.Size = 10.5
    $paragraph.Range.Font.Color = Get-RgbLong 31 58 95
    $paragraph.Range.Shading.BackgroundPatternColor = Get-RgbLong 244 246 249
    $paragraph.Format.LeftIndent = 12
    $paragraph.Format.RightIndent = 12
    $paragraph.Format.SpaceBefore = 6
    $paragraph.Format.SpaceAfter = 8
    $paragraph.Format.LineSpacingRule = 5
    $paragraph.Format.LineSpacing = 12.1
    return $paragraph
}

function Parse-TableCells([string]$Line) {
    $trimmed = $Line.Trim().Trim('|')
    return @($trimmed.Split('|') | ForEach-Object { Clean-Markdown $_ })
}

function Add-MarkdownTable($Document, [System.Collections.Generic.List[string]]$Lines) {
    $parsed = New-Object 'System.Collections.Generic.List[object]'
    foreach ($line in $Lines) {
        $cells = Parse-TableCells $line
        $separator = $true
        foreach ($cell in $cells) {
            if ($cell -notmatch '^:?-{3,}:?$') { $separator = $false; break }
        }
        if (-not $separator) { $parsed.Add($cells) }
    }
    if ($parsed.Count -eq 0) { return }

    $columnCount = $parsed[0].Count
    $table = $Document.Tables.Add($Document.Range($Document.Content.End - 1, $Document.Content.End - 1), $parsed.Count, $columnCount)
    $table.AllowAutoFit = 0
    $table.Borders.Enable = 1
    $table.TopPadding = 5
    $table.BottomPadding = 5
    $table.LeftPadding = 6
    $table.RightPadding = 6
    $table.Rows.AllowBreakAcrossPages = 0
    $table.Rows.Item(1).HeadingFormat = -1

    $widths = @()
    if ($columnCount -eq 2) { $widths = @(135, 333) }
    elseif ($columnCount -eq 3) { $widths = @(165, 75, 228) }
    elseif ($columnCount -eq 4) { $widths = @(125, 48, 65, 230) }
    else {
        $equal = 468 / $columnCount
        for ($w = 0; $w -lt $columnCount; $w++) { $widths += $equal }
    }

    for ($rowIndex = 0; $rowIndex -lt $parsed.Count; $rowIndex++) {
        $row = $parsed[$rowIndex]
        for ($columnIndex = 0; $columnIndex -lt $columnCount; $columnIndex++) {
            $cell = $table.Cell($rowIndex + 1, $columnIndex + 1)
            $cell.Range.Text = if ($columnIndex -lt $row.Count) { [string]$row[$columnIndex] } else { '' }
            $cell.Range.Font.Name = 'Calibri'
            $cellFontSize = if ($rowIndex -eq 0) { [single]9 } else { [single]9.5 }
            $cell.Range.Font.Size = $cellFontSize
            $cell.Range.ParagraphFormat.SpaceAfter = 2
            $cell.Range.ParagraphFormat.LineSpacingRule = 0
            $cell.VerticalAlignment = 1
            $cell.Width = $widths[$columnIndex]
            if ($rowIndex -eq 0) {
                $cell.Range.Font.Bold = -1
                $cell.Shading.BackgroundPatternColor = Get-RgbLong 242 244 247
            }
        }
    }
    $after = $Document.Paragraphs.Add()
    $after.Format.SpaceAfter = 6
}

function Configure-Document($Document) {
    $section = $Document.Sections.Item(1)
    $section.PageSetup.PageWidth = 612
    $section.PageSetup.PageHeight = 792
    $section.PageSetup.TopMargin = 72
    $section.PageSetup.BottomMargin = 72
    $section.PageSetup.LeftMargin = 72
    $section.PageSetup.RightMargin = 72
    $section.PageSetup.HeaderDistance = 35.424
    $section.PageSetup.FooterDistance = 35.424

    $normal = $Document.Styles.Item(-1)
    $normal.Font.Name = 'Calibri'
    $normal.Font.Size = 11
    $normal.Font.Color = Get-RgbLong 0 0 0
    $normal.ParagraphFormat.SpaceAfter = 6
    $normal.ParagraphFormat.LineSpacingRule = 5
    $normal.ParagraphFormat.LineSpacing = 12.1

    $header = $section.Headers.Item(1).Range
    $header.Text = 'Auditoría AEO y preparación para agentes | Observatorio CEPAL'
    $header.Font.Name = 'Calibri'
    $header.Font.Size = 9
    $header.Font.Color = Get-RgbLong 100 100 100
    $header.ParagraphFormat.Alignment = 0

    $footer = $section.Footers.Item(1).Range
    $footer.Text = '20 de agosto de 2026  |  '
    $footer.Font.Name = 'Calibri'
    $footer.Font.Size = 9
    $footer.Font.Color = Get-RgbLong 100 100 100
    $footer.ParagraphFormat.Alignment = 2
    $footer.Collapse(0)
    $footer.InsertAfter('Página ')
    $footer.Collapse(0)
    $section.Footers.Item(1).Range.Fields.Add($footer, 33) | Out-Null
}

function Add-Cover($Document) {
    $kicker = $Document.Paragraphs.Add()
    $kicker.Range.Text = 'AUDITORÍA TÉCNICA'
    $kicker.Range.Font.Name = 'Calibri'
    $kicker.Range.Font.Size = 10
    $kicker.Range.Font.Bold = -1
    $kicker.Range.Font.Color = Get-RgbLong 46 116 181
    $kicker.Format.SpaceBefore = 18
    $kicker.Format.SpaceAfter = 4

    $title = $Document.Paragraphs.Add()
    $title.Range.Text = 'Auditoría AEO y de preparación para agentes de IA'
    $title.Range.Font.Name = 'Calibri'
    $title.Range.Font.Size = 24
    $title.Range.Font.Bold = -1
    $title.Range.Font.Color = Get-RgbLong 0 0 0
    $title.Format.SpaceAfter = 5

    $subtitle = $Document.Paragraphs.Add()
    $subtitle.Range.Text = 'Observatorio Regional de Planificación para el Desarrollo de América Latina y el Caribe'
    $subtitle.Range.Font.Name = 'Calibri'
    $subtitle.Range.Font.Size = 13
    $subtitle.Range.Font.Color = Get-RgbLong 55 55 55
    $subtitle.Format.SpaceAfter = 16

    $metadata = @(
        @('Sitio', 'observatorioplanificacion.cepal.org'),
        @('Organización', 'Comisión Económica para América Latina y el Caribe (CEPAL)'),
        @('Fecha', '20 de agosto de 2026'),
        @('Estado', 'Informe vigente; sustituye la evaluación anterior')
    )
    foreach ($item in $metadata) {
        $paragraph = $Document.Paragraphs.Add()
        $label = $paragraph.Range
        $label.Text = "$($item[0]): "
        $label.Font.Name = 'Calibri'
        $label.Font.Size = 11
        $label.Font.Bold = -1
        $label.Collapse(0)
        $label.InsertAfter($item[1])
        $paragraph.Format.SpaceAfter = 3
    }

    $score = $Document.Paragraphs.Add()
    $score.Range.Text = '23/100  —  NO PREPARADO'
    $score.Range.Font.Name = 'Calibri'
    $score.Range.Font.Size = 18
    $score.Range.Font.Bold = -1
    $score.Range.Font.Color = Get-RgbLong 155 28 28
    $score.Range.Shading.BackgroundPatternColor = Get-RgbLong 252 235 235
    $score.Format.SpaceBefore = 18
    $score.Format.SpaceAfter = 8
    $score.Format.LeftIndent = 12

    Add-Callout $Document 'Este informe incorpora la implementación dinámica actual: shells HTML, fragmentos cargados con JavaScript, filtros, fichas por selección, API Kobo, estados HTTP y capacidad de recuperación sin ejecutar la aplicación completa.' | Out-Null

    $Document.Paragraphs.Add().Range.InsertBreak(7)
}

$markdown = Get-Content -LiteralPath $MarkdownPath -Raw -Encoding UTF8
$lines = $markdown -split "`r?`n"
$word = $null
$document = $null

try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Add()
    Configure-Document $document
    Add-Cover $document

    $start = 0
    for ($scan = 0; $scan -lt $lines.Count; $scan++) {
        if ($lines[$scan] -eq '## 1. Resumen ejecutivo') { $start = $scan; break }
    }

    $index = $start
    while ($index -lt $lines.Count) {
        $line = $lines[$index]
        if ([string]::IsNullOrWhiteSpace($line) -or $line.Trim() -eq '---') {
            $index++
            continue
        }

        if ($line.Trim().StartsWith('|')) {
            $tableLines = New-Object 'System.Collections.Generic.List[string]'
            while ($index -lt $lines.Count -and $lines[$index].Trim().StartsWith('|')) {
                $tableLines.Add($lines[$index])
                $index++
            }
            Add-MarkdownTable $document $tableLines
            continue
        }

        if ($line.Trim() -eq '```' -or $line.Trim().StartsWith('```')) {
            $codeLines = New-Object 'System.Collections.Generic.List[string]'
            $index++
            while ($index -lt $lines.Count -and -not $lines[$index].Trim().StartsWith('```')) {
                $codeLines.Add($lines[$index])
                $index++
            }
            if ($index -lt $lines.Count) { $index++ }
            Add-CodeBlock $document $codeLines.ToArray() | Out-Null
            continue
        }

        if ($line -match '^####\s+(.+)$') { Add-HeadingText $document $Matches[1] 3 | Out-Null; $index++; continue }
        if ($line -match '^###\s+(.+)$') { Add-HeadingText $document $Matches[1] 2 | Out-Null; $index++; continue }
        if ($line -match '^##\s+(.+)$') { Add-HeadingText $document $Matches[1] 1 | Out-Null; $index++; continue }
        if ($line -match '^>\s*(.+)$') { Add-Callout $document $Matches[1] | Out-Null; $index++; continue }
        if ($line -match '^\s*-\s+(.+)$') { Add-ListItem $document $Matches[1] $false | Out-Null; $index++; continue }
        if ($line -match '^\s*\d+\.\s+(.+)$') { Add-ListItem $document $Matches[1] $true | Out-Null; $index++; continue }

        $paragraphLines = New-Object 'System.Collections.Generic.List[string]'
        while ($index -lt $lines.Count) {
            $candidate = $lines[$index]
            if ([string]::IsNullOrWhiteSpace($candidate) -or $candidate.Trim() -eq '---' -or $candidate.Trim().StartsWith('|') -or $candidate.Trim().StartsWith('```') -or $candidate -match '^#{2,4}\s+' -or $candidate -match '^>\s*' -or $candidate -match '^\s*-\s+' -or $candidate -match '^\s*\d+\.\s+') { break }
            $paragraphLines.Add($candidate.Trim())
            $index++
        }
        if ($paragraphLines.Count -gt 0) {
            Add-ParagraphText $document ($paragraphLines -join ' ') | Out-Null
        }
        else {
            $index++
        }
    }

    $document.BuiltInDocumentProperties.Item('Title').Value = 'Auditoría AEO y de preparación para agentes de IA — Observatorio CEPAL'
    $document.BuiltInDocumentProperties.Item('Subject').Value = 'Evaluación del portal dinámico, API, AEO y preparación para agentes'
    $document.BuiltInDocumentProperties.Item('Author').Value = 'OpenAI Codex'
    $document.SaveAs2($DocxPath, 16)
    $document.ExportAsFixedFormat($PdfPath, 17)
}
finally {
    if ($document -ne $null) { $document.Close(0) }
    if ($word -ne $null) { $word.Quit() }
    if ($document -ne $null) { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($document) }
    if ($word -ne $null) { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

Write-Output $DocxPath
Write-Output $PdfPath
