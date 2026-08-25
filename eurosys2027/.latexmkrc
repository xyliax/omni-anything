my $root = $ENV{'PWD'};
$ENV{'TEXINPUTS'} = "$root/vendor/acmart//:" . ($ENV{'TEXINPUTS'} // '');
$ENV{'BSTINPUTS'} = "$root/vendor/acmart//:" . ($ENV{'BSTINPUTS'} // '');
$pdf_mode = 1;
