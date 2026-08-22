param([Parameter(Mandatory=$true)][string]$MarkdownPath,[Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.IO.Compression
$fence=[string][char]96+[string][char]96+[string][char]96
function X([string]$t){if($null-eq$t){return''};[Security.SecurityElement]::Escape($t)}
function Clean([string]$t){$v=[regex]::Replace($t,'\[([^\]]+)\]\((https?://[^\)]+)\)','$1 ($2)');$v=[regex]::Replace($v,'<(https?://[^>]+)>','$1');$v.Replace('**','').Replace([string][char]96,'').Trim()}
function Run([string]$t,[bool]$b=$false,[string]$font='Calibri',[int]$size=22,[string]$color='000000'){
 $bx=if($b){'<w:b/>'}else{''}
 '<w:r><w:rPr><w:rFonts w:ascii='+$font+' w:hAnsi='+$font+'/>'+$bx+'<w:color w:val='+$color+'/><w:sz w:val='+$size+'/></w:rPr><w:t xml:space=preserve>'+(X $t)+'</w:t></w:r>'
}
function Para([string]$t,[string]$style='Normal',[int]$before=0,[int]$after=120,[string]$extra=''){
 '<w:p><w:pPr><w:pStyle w:val='+$style+'/><w:spacing w:before='+$before+' w:after='+$after+' w:line=264 w:lineRule=auto/><w:widowControl/>'+$extra+'</w:pPr>'+(Run (Clean $t))+'</w:p>'
}
function ListPara([string]$t,[int]$id){Para $t 'Normal' 0 160 ('<w:numPr><w:ilvl w:val=0/><w:numId w:val='+$id+'/></w:numPr><w:ind w:left=720 w:hanging=360/>')}
function Table([Collections.Generic.List[string]]$lines){
 $rows=New-Object 'Collections.Generic.List[object]'
 foreach($line in $lines){$cells=@($line.Trim().Trim('|').Split('|')|ForEach-Object{Clean $_});$sep=$true;foreach($cell in $cells){if($cell-notmatch'^:?-{3,}:?$'){$sep=$false;break}};if(-not$sep){$rows.Add($cells)}}
 if($rows.Count-eq0){return''};$n=$rows[0].Count
 if($n-eq2){$widths=@(2700,6660)}elseif($n-eq3){$widths=@(3300,1500,4560)}elseif($n-eq4){$widths=@(2500,960,1300,4600)}else{$widths=@();$each=[math]::Floor(9360/$n);for($a=0;$a-lt$n;$a++){$widths+=$each}}
 $grid='';foreach($w in $widths){$grid+='<w:gridCol w:w='+$w+'/>'}
 $xml='<w:tbl><w:tblPr><w:tblW w:w=9360 w:type=dxa/><w:tblInd w:w=120 w:type=dxa/><w:tblLayout w:type=fixed/><w:tblBorders><w:top w:val=single w:sz=4 w:color=B7C3D0/><w:left w:val=single w:sz=4 w:color=B7C3D0/><w:bottom w:val=single w:sz=4 w:color=B7C3D0/><w:right w:val=single w:sz=4 w:color=B7C3D0/><w:insideH w:val=single w:sz=4 w:color=D4DAE1/><w:insideV w:val=single w:sz=4 w:color=D4DAE1/></w:tblBorders></w:tblPr><w:tblGrid>'+$grid+'</w:tblGrid>'
 for($r=0;$r-lt$rows.Count;$r++){$xml+='<w:tr><w:trPr><w:cantSplit/>'+$(if($r-eq0){'<w:tblHeader/>'}else{''})+'</w:trPr>';for($c=0;$c-lt$n;$c++){$text=if($c-lt$rows[$r].Count){[string]$rows[$r][$c]}else{''};$shade=if($r-eq0){'<w:shd w:val=clear w:fill=F2F4F7/>'}else{''};$xml+='<w:tc><w:tcPr><w:tcW w:w='+$widths[$c]+' w:type=dxa/>'+$shade+'</w:tcPr><w:p>'+(Run $text ($r-eq0) 'Calibri' 19)+'</w:p></w:tc>'};$xml+='</w:tr>'}
 $xml+'</w:tbl><w:p><w:pPr><w:spacing w:after=120/></w:pPr></w:p>'
}
function Entry($zip,[string]$name,[string]$content){$item=$zip.CreateEntry($name);$s=$item.Open();$w=New-Object IO.StreamWriter($s,(New-Object Text.UTF8Encoding($false)));try{$w.Write($content)}finally{$w.Dispose();$s.Dispose()}}
$lines=(Get-Content -LiteralPath $MarkdownPath -Raw -Encoding UTF8)-split'\r?\n'
$body=New-Object Text.StringBuilder
[void]$body.Append((Para 'AUDITORIA TECNICA' 'Kicker' 360 80))
[void]$body.Append((Para 'Auditoria AEO y de preparacion para agentes de IA' 'Title' 0 100))
[void]$body.Append((Para 'Observatorio Regional de Planificacion para el Desarrollo de America Latina y el Caribe' 'Subtitle' 0 320))
[void]$body.Append((Para 'Sitio: observatorioplanificacion.cepal.org' 'Normal' 0 60))
[void]$body.Append((Para 'Organizacion: Comision Economica para America Latina y el Caribe (CEPAL)' 'Normal' 0 60))
[void]$body.Append((Para 'Fecha: 20 de agosto de 2026' 'Normal' 0 60))
[void]$body.Append((Para 'Estado: informe vigente; sustituye la evaluacion anterior' 'Normal' 0 240))
[void]$body.Append((Para '23/100 - NO PREPARADO' 'Score' 120 160 '<w:shd w:val=clear w:fill=FCEBEB/><w:ind w:left=160/>'))
[void]$body.Append((Para 'Este informe incorpora shells HTML, JavaScript, filtros, fichas por seleccion, API Kobo, estados HTTP y recuperacion por agentes.' 'Quote' 80 160 '<w:shd w:val=clear w:fill=F4F6F9/><w:ind w:left=200 w:right=200/>'))
[void]$body.Append('<w:p><w:r><w:br w:type=page/></w:r></w:p>')
$start=0;for($scan=0;$scan-lt$lines.Count;$scan++){if($lines[$scan]-eq'## 1. Resumen ejecutivo'){$start=$scan;break}}
$i=$start
while($i-lt$lines.Count){
 $line=$lines[$i]
 if([string]::IsNullOrWhiteSpace($line)-or$line.Trim()-eq'---'){$i++;continue}
 if($line.Trim().StartsWith('|')){$tl=New-Object 'Collections.Generic.List[string]';while($i-lt$lines.Count-and$lines[$i].Trim().StartsWith('|')){$tl.Add($lines[$i]);$i++};[void]$body.Append((Table $tl));continue}
 if($line.Trim().StartsWith($fence)){$code=New-Object 'Collections.Generic.List[string]';$i++;while($i-lt$lines.Count-and-not$lines[$i].Trim().StartsWith($fence)){$code.Add($lines[$i]);$i++};if($i-lt$lines.Count){$i++};[void]$body.Append((Para ($code-join[Environment]::NewLine) 'Code' 80 160 '<w:shd w:val=clear w:fill=F2F4F7/>'));continue}
 if($line-match'^####\s+(.+)$'){[void]$body.Append((Para $Matches[1] 'Heading3' 160 80));$i++;continue}
 if($line-match'^###\s+(.+)$'){[void]$body.Append((Para $Matches[1] 'Heading2' 240 120));$i++;continue}
 if($line-match'^##\s+(.+)$'){[void]$body.Append((Para $Matches[1] 'Heading1' 320 160));$i++;continue}
 if($line-match'^>\s*(.+)$'){[void]$body.Append((Para $Matches[1] 'Quote' 80 160 '<w:shd w:val=clear w:fill=F4F6F9/>'));$i++;continue}
 if($line-match'^\s*-\s+(.+)$'){[void]$body.Append((ListPara $Matches[1] 1));$i++;continue}
 if($line-match'^\s*\d+\.\s+(.+)$'){[void]$body.Append((ListPara $Matches[1] 2));$i++;continue}
 $parts=New-Object 'Collections.Generic.List[string]'
 while($i-lt$lines.Count){$c=$lines[$i];if([string]::IsNullOrWhiteSpace($c)-or$c.Trim()-eq'---'-or$c.Trim().StartsWith('|')-or$c.Trim().StartsWith($fence)-or$c-match'^#{2,4}\s+'-or$c-match'^>\s*'-or$c-match'^\s*-\s+'-or$c-match'^\s*\d+\.\s+'){break};$parts.Add($c.Trim());$i++}
 if($parts.Count-gt0){[void]$body.Append((Para ($parts-join' ') 'Normal' 0 120))}else{$i++}
}
$styles='<?xml version=1.0 encoding=UTF-8 standalone=yes?><w:styles xmlns:w=http://schemas.openxmlformats.org/wordprocessingml/2006/main><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii=Calibri w:hAnsi=Calibri/><w:sz w:val=22/></w:rPr></w:rPrDefault></w:docDefaults><w:style w:type=paragraph w:default=1 w:styleId=Normal><w:name w:val=Normal/><w:qFormat/><w:pPr><w:spacing w:after=120 w:line=264 w:lineRule=auto/></w:pPr><w:rPr><w:rFonts w:ascii=Calibri w:hAnsi=Calibri/><w:sz w:val=22/></w:rPr></w:style>'
$styles+='<w:style w:type=paragraph w:styleId=Title><w:name w:val=Title/><w:basedOn w:val=Normal/><w:qFormat/><w:rPr><w:b/><w:sz w:val=48/></w:rPr></w:style><w:style w:type=paragraph w:styleId=Subtitle><w:name w:val=Subtitle/><w:basedOn w:val=Normal/><w:qFormat/><w:rPr><w:sz w:val=26/><w:color w:val=373737/></w:rPr></w:style><w:style w:type=paragraph w:styleId=Kicker><w:name w:val=Kicker/><w:basedOn w:val=Normal/><w:qFormat/><w:rPr><w:b/><w:sz w:val=20/><w:color w:val=2E74B5/></w:rPr></w:style>'
