graph [
  node_attrs_setting [
    name "cpu"
    distribution "uniform"
    dtype "int"
    generative 1
    high 100
    low 50
    owner "node"
    type "resource"
  ]
  node_attrs_setting [
    name "max_cpu"
    originator "cpu"
    owner "node"
    type "extrema"
  ]
  link_attrs_setting [
    distribution "uniform"
    dtype "int"
    generative 1
    high 100
    low 50
    name "bw"
    owner "link"
    type "resource"
  ]
  link_attrs_setting [
    name "max_bw"
    originator "bw"
    owner "link"
    type "extrema"
  ]
  save_dir "dataset/p_net"
  topology [
    type "waxman"
    wm_alpha 0.5
    wm_beta 0.2
  ]
  file_name "p_net.gml"
  num_nodes 100
  type "waxman"
  wm_alpha 0.5
  wm_beta 0.2
  node [
    id 0
    label "0"
    pos 0.6394267984578837
    pos 0.025010755222666936
    cpu 62
    max_cpu 62
  ]
  node [
    id 1
    label "1"
    pos 0.27502931836911926
    pos 0.22321073814882275
    cpu 53
    max_cpu 53
  ]
  node [
    id 2
    label "2"
    pos 0.7364712141640124
    pos 0.6766994874229113
    cpu 85
    max_cpu 85
  ]
  node [
    id 3
    label "3"
    pos 0.8921795677048454
    pos 0.08693883262941615
    cpu 59
    max_cpu 59
  ]
  node [
    id 4
    label "4"
    pos 0.4219218196852704
    pos 0.029797219438070344
    cpu 73
    max_cpu 73
  ]
  node [
    id 5
    label "5"
    pos 0.21863797480360336
    pos 0.5053552881033624
    cpu 71
    max_cpu 71
  ]
  node [
    id 6
    label "6"
    pos 0.026535969683863625
    pos 0.1988376506866485
    cpu 84
    max_cpu 84
  ]
  node [
    id 7
    label "7"
    pos 0.6498844377795232
    pos 0.5449414806032167
    cpu 55
    max_cpu 55
  ]
  node [
    id 8
    label "8"
    pos 0.2204406220406967
    pos 0.5892656838759087
    cpu 73
    max_cpu 73
  ]
  node [
    id 9
    label "9"
    pos 0.8094304566778266
    pos 0.006498759678061017
    cpu 87
    max_cpu 87
  ]
  node [
    id 10
    label "10"
    pos 0.8058192518328079
    pos 0.6981393949882269
    cpu 52
    max_cpu 52
  ]
  node [
    id 11
    label "11"
    pos 0.3402505165179919
    pos 0.15547949981178155
    cpu 81
    max_cpu 81
  ]
  node [
    id 12
    label "12"
    pos 0.9572130722067812
    pos 0.33659454511262676
    cpu 65
    max_cpu 65
  ]
  node [
    id 13
    label "13"
    pos 0.09274584338014791
    pos 0.09671637683346401
    cpu 85
    max_cpu 85
  ]
  node [
    id 14
    label "14"
    pos 0.8474943663474598
    pos 0.6037260313668911
    cpu 76
    max_cpu 76
  ]
  node [
    id 15
    label "15"
    pos 0.8071282732743802
    pos 0.7297317866938179
    cpu 69
    max_cpu 69
  ]
  node [
    id 16
    label "16"
    pos 0.5362280914547007
    pos 0.9731157639793706
    cpu 72
    max_cpu 72
  ]
  node [
    id 17
    label "17"
    pos 0.3785343772083535
    pos 0.552040631273227
    cpu 95
    max_cpu 95
  ]
  node [
    id 18
    label "18"
    pos 0.8294046642529949
    pos 0.6185197523642461
    cpu 92
    max_cpu 92
  ]
  node [
    id 19
    label "19"
    pos 0.8617069003107772
    pos 0.577352145256762
    cpu 76
    max_cpu 76
  ]
  node [
    id 20
    label "20"
    pos 0.7045718362149235
    pos 0.045824383655662215
    cpu 91
    max_cpu 91
  ]
  node [
    id 21
    label "21"
    pos 0.22789827565154686
    pos 0.28938796360210717
    cpu 72
    max_cpu 72
  ]
  node [
    id 22
    label "22"
    pos 0.0797919769236275
    pos 0.23279088636103018
    cpu 68
    max_cpu 68
  ]
  node [
    id 23
    label "23"
    pos 0.10100142940972912
    pos 0.2779736031100921
    cpu 59
    max_cpu 59
  ]
  node [
    id 24
    label "24"
    pos 0.6356844442644002
    pos 0.36483217897008424
    cpu 62
    max_cpu 62
  ]
  node [
    id 25
    label "25"
    pos 0.37018096711688264
    pos 0.2095070307714877
    cpu 100
    max_cpu 100
  ]
  node [
    id 26
    label "26"
    pos 0.26697782204911336
    pos 0.936654587712494
    cpu 70
    max_cpu 70
  ]
  node [
    id 27
    label "27"
    pos 0.6480353852465935
    pos 0.6091310056669882
    cpu 73
    max_cpu 73
  ]
  node [
    id 28
    label "28"
    pos 0.171138648198097
    pos 0.7291267979503492
    cpu 92
    max_cpu 92
  ]
  node [
    id 29
    label "29"
    pos 0.1634024937619284
    pos 0.3794554417576478
    cpu 95
    max_cpu 95
  ]
  node [
    id 30
    label "30"
    pos 0.9895233506365952
    pos 0.6399997598540929
    cpu 81
    max_cpu 81
  ]
  node [
    id 31
    label "31"
    pos 0.5569497437746462
    pos 0.6846142509898746
    cpu 91
    max_cpu 91
  ]
  node [
    id 32
    label "32"
    pos 0.8428519201898096
    pos 0.7759999115462448
    cpu 62
    max_cpu 62
  ]
  node [
    id 33
    label "33"
    pos 0.22904807196410437
    pos 0.03210024390403776
    cpu 87
    max_cpu 87
  ]
  node [
    id 34
    label "34"
    pos 0.3154530480590819
    pos 0.26774087597570273
    cpu 72
    max_cpu 72
  ]
  node [
    id 35
    label "35"
    pos 0.21098284358632646
    pos 0.9429097143350544
    cpu 63
    max_cpu 63
  ]
  node [
    id 36
    label "36"
    pos 0.8763676264726689
    pos 0.3146778807984779
    cpu 98
    max_cpu 98
  ]
  node [
    id 37
    label "37"
    pos 0.65543866529488
    pos 0.39563190106066426
    cpu 76
    max_cpu 76
  ]
  node [
    id 38
    label "38"
    pos 0.9145475897405435
    pos 0.4588518525873988
    cpu 86
    max_cpu 86
  ]
  node [
    id 39
    label "39"
    pos 0.26488016649805246
    pos 0.24662750769398345
    cpu 91
    max_cpu 91
  ]
  node [
    id 40
    label "40"
    pos 0.5613681341631508
    pos 0.26274160852293527
    cpu 70
    max_cpu 70
  ]
  node [
    id 41
    label "41"
    pos 0.5845859902235405
    pos 0.897822883602477
    cpu 83
    max_cpu 83
  ]
  node [
    id 42
    label "42"
    pos 0.39940050514039727
    pos 0.21932075915728333
    cpu 62
    max_cpu 62
  ]
  node [
    id 43
    label "43"
    pos 0.9975376064951103
    pos 0.5095262936764645
    cpu 82
    max_cpu 82
  ]
  node [
    id 44
    label "44"
    pos 0.09090941217379389
    pos 0.04711637542473457
    cpu 75
    max_cpu 75
  ]
  node [
    id 45
    label "45"
    pos 0.10964913035065915
    pos 0.62744604170309
    cpu 61
    max_cpu 61
  ]
  node [
    id 46
    label "46"
    pos 0.7920793643629641
    pos 0.42215996679968404
    cpu 100
    max_cpu 100
  ]
  node [
    id 47
    label "47"
    pos 0.06352770615195713
    pos 0.38161928650653676
    cpu 98
    max_cpu 98
  ]
  node [
    id 48
    label "48"
    pos 0.9961213802400968
    pos 0.529114345099137
    cpu 94
    max_cpu 94
  ]
  node [
    id 49
    label "49"
    pos 0.9710783776136181
    pos 0.8607797022344981
    cpu 50
    max_cpu 50
  ]
  node [
    id 50
    label "50"
    pos 0.011481021942819636
    pos 0.7207218193601946
    cpu 80
    max_cpu 80
  ]
  node [
    id 51
    label "51"
    pos 0.6817103690265748
    pos 0.5369703304087952
    cpu 94
    max_cpu 94
  ]
  node [
    id 52
    label "52"
    pos 0.2668251899525428
    pos 0.6409617985798081
    cpu 100
    max_cpu 100
  ]
  node [
    id 53
    label "53"
    pos 0.11155217359587644
    pos 0.434765250669105
    cpu 69
    max_cpu 69
  ]
  node [
    id 54
    label "54"
    pos 0.45372370632920644
    pos 0.9538159275210801
    cpu 73
    max_cpu 73
  ]
  node [
    id 55
    label "55"
    pos 0.8758529403781941
    pos 0.26338905075109076
    cpu 73
    max_cpu 73
  ]
  node [
    id 56
    label "56"
    pos 0.5005861130502983
    pos 0.17865188053013137
    cpu 97
    max_cpu 97
  ]
  node [
    id 57
    label "57"
    pos 0.9126278393448205
    pos 0.8705185698367669
    cpu 60
    max_cpu 60
  ]
  node [
    id 58
    label "58"
    pos 0.2984447914486329
    pos 0.6389494948660052
    cpu 55
    max_cpu 55
  ]
  node [
    id 59
    label "59"
    pos 0.6089702114381723
    pos 0.1528392685496348
    cpu 67
    max_cpu 67
  ]
  node [
    id 60
    label "60"
    pos 0.7625108000751513
    pos 0.5393790301196257
    cpu 94
    max_cpu 94
  ]
  node [
    id 61
    label "61"
    pos 0.7786264786305582
    pos 0.5303536721951775
    cpu 55
    max_cpu 55
  ]
  node [
    id 62
    label "62"
    pos 0.0005718961279435053
    pos 0.3241560570046731
    cpu 80
    max_cpu 80
  ]
  node [
    id 63
    label "63"
    pos 0.019476742385832302
    pos 0.9290986162646171
    cpu 71
    max_cpu 71
  ]
  node [
    id 64
    label "64"
    pos 0.8787218778231842
    pos 0.8316655293611794
    cpu 72
    max_cpu 72
  ]
  node [
    id 65
    label "65"
    pos 0.30751412540266143
    pos 0.05792516649418755
    cpu 91
    max_cpu 91
  ]
  node [
    id 66
    label "66"
    pos 0.8780095992040405
    pos 0.9469494452979941
    cpu 66
    max_cpu 66
  ]
  node [
    id 67
    label "67"
    pos 0.08565345206787878
    pos 0.4859904633166138
    cpu 85
    max_cpu 85
  ]
  node [
    id 68
    label "68"
    pos 0.06921251846838361
    pos 0.7606021652572316
    cpu 54
    max_cpu 54
  ]
  node [
    id 69
    label "69"
    pos 0.7658344293069878
    pos 0.1283914644997628
    cpu 53
    max_cpu 53
  ]
  node [
    id 70
    label "70"
    pos 0.4752823780987313
    pos 0.5498035934949439
    cpu 55
    max_cpu 55
  ]
  node [
    id 71
    label "71"
    pos 0.2650566289400591
    pos 0.8724330410852574
    cpu 97
    max_cpu 97
  ]
  node [
    id 72
    label "72"
    pos 0.4231379402008869
    pos 0.21179820544208205
    cpu 53
    max_cpu 53
  ]
  node [
    id 73
    label "73"
    pos 0.5392960887794583
    pos 0.7299310690899762
    cpu 65
    max_cpu 65
  ]
  node [
    id 74
    label "74"
    pos 0.2011510633896959
    pos 0.31171629130089495
    cpu 93
    max_cpu 93
  ]
  node [
    id 75
    label "75"
    pos 0.9951493566608947
    pos 0.6498780576394535
    cpu 62
    max_cpu 62
  ]
  node [
    id 76
    label "76"
    pos 0.43810008391450406
    pos 0.5175758410355906
    cpu 60
    max_cpu 60
  ]
  node [
    id 77
    label "77"
    pos 0.12100419586826572
    pos 0.22469733703155736
    cpu 96
    max_cpu 96
  ]
  node [
    id 78
    label "78"
    pos 0.33808556214745533
    pos 0.5883087184572333
    cpu 77
    max_cpu 77
  ]
  node [
    id 79
    label "79"
    pos 0.230114732596577
    pos 0.22021738445155947
    cpu 73
    max_cpu 73
  ]
  node [
    id 80
    label "80"
    pos 0.07099308600903254
    pos 0.6311029572700989
    cpu 93
    max_cpu 93
  ]
  node [
    id 81
    label "81"
    pos 0.22894178381115438
    pos 0.905420013006128
    cpu 73
    max_cpu 73
  ]
  node [
    id 82
    label "82"
    pos 0.8596354002537465
    pos 0.07085734988865344
    cpu 93
    max_cpu 93
  ]
  node [
    id 83
    label "83"
    pos 0.23800463436899522
    pos 0.6689777782962806
    cpu 64
    max_cpu 64
  ]
  node [
    id 84
    label "84"
    pos 0.2142368073704386
    pos 0.132311848725025
    cpu 70
    max_cpu 70
  ]
  node [
    id 85
    label "85"
    pos 0.935514240580671
    pos 0.5710430933252845
    cpu 55
    max_cpu 55
  ]
  node [
    id 86
    label "86"
    pos 0.47267102631179414
    pos 0.7846194242907534
    cpu 84
    max_cpu 84
  ]
  node [
    id 87
    label "87"
    pos 0.8074969977666434
    pos 0.1904099143618777
    cpu 55
    max_cpu 55
  ]
  node [
    id 88
    label "88"
    pos 0.09693081422882333
    pos 0.4310511824063775
    cpu 56
    max_cpu 56
  ]
  node [
    id 89
    label "89"
    pos 0.4235786230199208
    pos 0.467024668036675
    cpu 88
    max_cpu 88
  ]
  node [
    id 90
    label "90"
    pos 0.7290758494598506
    pos 0.6733645472933015
    cpu 53
    max_cpu 53
  ]
  node [
    id 91
    label "91"
    pos 0.9841652113659661
    pos 0.09841787115195888
    cpu 71
    max_cpu 71
  ]
  node [
    id 92
    label "92"
    pos 0.4026212821022688
    pos 0.33930260539496315
    cpu 90
    max_cpu 90
  ]
  node [
    id 93
    label "93"
    pos 0.8616725363527911
    pos 0.24865633392028563
    cpu 59
    max_cpu 59
  ]
  node [
    id 94
    label "94"
    pos 0.1902089084408115
    pos 0.4486135478331319
    cpu 68
    max_cpu 68
  ]
  node [
    id 95
    label "95"
    pos 0.4218816398344042
    pos 0.27854514466694047
    cpu 70
    max_cpu 70
  ]
  node [
    id 96
    label "96"
    pos 0.2498064478821005
    pos 0.9232655992760128
    cpu 86
    max_cpu 86
  ]
  node [
    id 97
    label "97"
    pos 0.44313074505345695
    pos 0.8613491047618306
    cpu 90
    max_cpu 90
  ]
  node [
    id 98
    label "98"
    pos 0.5503253124498481
    pos 0.05058832952488124
    cpu 96
    max_cpu 96
  ]
  node [
    id 99
    label "99"
    pos 0.9992824684127266
    pos 0.8360275850799519
    cpu 50
    max_cpu 50
  ]
  edge [
    source 0
    target 4
    bw 65
    max_bw 65
  ]
  edge [
    source 0
    target 20
    bw 95
    max_bw 95
  ]
  edge [
    source 0
    target 25
    bw 82
    max_bw 82
  ]
  edge [
    source 0
    target 59
    bw 98
    max_bw 98
  ]
  edge [
    source 0
    target 70
    bw 99
    max_bw 99
  ]
  edge [
    source 0
    target 82
    bw 69
    max_bw 69
  ]
  edge [
    source 0
    target 91
    bw 56
    max_bw 56
  ]
  edge [
    source 0
    target 98
    bw 78
    max_bw 78
  ]
  edge [
    source 1
    target 21
    bw 73
    max_bw 73
  ]
  edge [
    source 1
    target 27
    bw 74
    max_bw 74
  ]
  edge [
    source 1
    target 34
    bw 74
    max_bw 74
  ]
  edge [
    source 1
    target 39
    bw 73
    max_bw 73
  ]
  edge [
    source 1
    target 42
    bw 51
    max_bw 51
  ]
  edge [
    source 1
    target 45
    bw 53
    max_bw 53
  ]
  edge [
    source 1
    target 56
    bw 91
    max_bw 91
  ]
  edge [
    source 1
    target 71
    bw 59
    max_bw 59
  ]
  edge [
    source 1
    target 78
    bw 63
    max_bw 63
  ]
  edge [
    source 1
    target 84
    bw 61
    max_bw 61
  ]
  edge [
    source 1
    target 89
    bw 91
    max_bw 91
  ]
  edge [
    source 1
    target 97
    bw 55
    max_bw 55
  ]
  edge [
    source 2
    target 7
    bw 55
    max_bw 55
  ]
  edge [
    source 2
    target 12
    bw 86
    max_bw 86
  ]
  edge [
    source 2
    target 15
    bw 56
    max_bw 56
  ]
  edge [
    source 2
    target 19
    bw 92
    max_bw 92
  ]
  edge [
    source 2
    target 21
    bw 66
    max_bw 66
  ]
  edge [
    source 2
    target 31
    bw 96
    max_bw 96
  ]
  edge [
    source 2
    target 33
    bw 55
    max_bw 55
  ]
  edge [
    source 2
    target 36
    bw 71
    max_bw 71
  ]
  edge [
    source 2
    target 41
    bw 76
    max_bw 76
  ]
  edge [
    source 2
    target 60
    bw 52
    max_bw 52
  ]
  edge [
    source 2
    target 66
    bw 64
    max_bw 64
  ]
  edge [
    source 2
    target 75
    bw 71
    max_bw 71
  ]
  edge [
    source 2
    target 87
    bw 98
    max_bw 98
  ]
  edge [
    source 2
    target 99
    bw 67
    max_bw 67
  ]
  edge [
    source 3
    target 9
    bw 71
    max_bw 71
  ]
  edge [
    source 3
    target 11
    bw 50
    max_bw 50
  ]
  edge [
    source 3
    target 14
    bw 100
    max_bw 100
  ]
  edge [
    source 3
    target 18
    bw 92
    max_bw 92
  ]
  edge [
    source 3
    target 20
    bw 70
    max_bw 70
  ]
  edge [
    source 3
    target 38
    bw 87
    max_bw 87
  ]
  edge [
    source 3
    target 59
    bw 79
    max_bw 79
  ]
  edge [
    source 3
    target 93
    bw 58
    max_bw 58
  ]
  edge [
    source 4
    target 13
    bw 95
    max_bw 95
  ]
  edge [
    source 4
    target 23
    bw 80
    max_bw 80
  ]
  edge [
    source 4
    target 42
    bw 87
    max_bw 87
  ]
  edge [
    source 4
    target 52
    bw 72
    max_bw 72
  ]
  edge [
    source 4
    target 65
    bw 82
    max_bw 82
  ]
  edge [
    source 4
    target 98
    bw 72
    max_bw 72
  ]
  edge [
    source 4
    target 99
    bw 60
    max_bw 60
  ]
  edge [
    source 5
    target 8
    bw 97
    max_bw 97
  ]
  edge [
    source 5
    target 24
    bw 55
    max_bw 55
  ]
  edge [
    source 5
    target 29
    bw 89
    max_bw 89
  ]
  edge [
    source 5
    target 37
    bw 81
    max_bw 81
  ]
  edge [
    source 5
    target 58
    bw 55
    max_bw 55
  ]
  edge [
    source 5
    target 89
    bw 56
    max_bw 56
  ]
  edge [
    source 5
    target 96
    bw 68
    max_bw 68
  ]
  edge [
    source 6
    target 22
    bw 50
    max_bw 50
  ]
  edge [
    source 6
    target 33
    bw 54
    max_bw 54
  ]
  edge [
    source 6
    target 45
    bw 92
    max_bw 92
  ]
  edge [
    source 6
    target 79
    bw 57
    max_bw 57
  ]
  edge [
    source 6
    target 80
    bw 65
    max_bw 65
  ]
  edge [
    source 6
    target 92
    bw 77
    max_bw 77
  ]
  edge [
    source 7
    target 14
    bw 81
    max_bw 81
  ]
  edge [
    source 7
    target 18
    bw 57
    max_bw 57
  ]
  edge [
    source 7
    target 51
    bw 73
    max_bw 73
  ]
  edge [
    source 7
    target 92
    bw 98
    max_bw 98
  ]
  edge [
    source 8
    target 11
    bw 53
    max_bw 53
  ]
  edge [
    source 8
    target 16
    bw 72
    max_bw 72
  ]
  edge [
    source 8
    target 21
    bw 55
    max_bw 55
  ]
  edge [
    source 8
    target 25
    bw 84
    max_bw 84
  ]
  edge [
    source 8
    target 40
    bw 74
    max_bw 74
  ]
  edge [
    source 8
    target 45
    bw 84
    max_bw 84
  ]
  edge [
    source 8
    target 52
    bw 50
    max_bw 50
  ]
  edge [
    source 8
    target 58
    bw 57
    max_bw 57
  ]
  edge [
    source 8
    target 63
    bw 84
    max_bw 84
  ]
  edge [
    source 8
    target 71
    bw 78
    max_bw 78
  ]
  edge [
    source 8
    target 74
    bw 90
    max_bw 90
  ]
  edge [
    source 8
    target 76
    bw 58
    max_bw 58
  ]
  edge [
    source 8
    target 78
    bw 78
    max_bw 78
  ]
  edge [
    source 8
    target 79
    bw 73
    max_bw 73
  ]
  edge [
    source 8
    target 83
    bw 80
    max_bw 80
  ]
  edge [
    source 8
    target 84
    bw 79
    max_bw 79
  ]
  edge [
    source 8
    target 94
    bw 53
    max_bw 53
  ]
  edge [
    source 9
    target 20
    bw 56
    max_bw 56
  ]
  edge [
    source 9
    target 40
    bw 82
    max_bw 82
  ]
  edge [
    source 9
    target 46
    bw 71
    max_bw 71
  ]
  edge [
    source 9
    target 56
    bw 78
    max_bw 78
  ]
  edge [
    source 9
    target 69
    bw 66
    max_bw 66
  ]
  edge [
    source 9
    target 88
    bw 69
    max_bw 69
  ]
  edge [
    source 10
    target 14
    bw 80
    max_bw 80
  ]
  edge [
    source 10
    target 15
    bw 50
    max_bw 50
  ]
  edge [
    source 10
    target 19
    bw 50
    max_bw 50
  ]
  edge [
    source 10
    target 31
    bw 72
    max_bw 72
  ]
  edge [
    source 10
    target 34
    bw 80
    max_bw 80
  ]
  edge [
    source 10
    target 40
    bw 51
    max_bw 51
  ]
  edge [
    source 10
    target 48
    bw 59
    max_bw 59
  ]
  edge [
    source 10
    target 51
    bw 90
    max_bw 90
  ]
  edge [
    source 10
    target 59
    bw 76
    max_bw 76
  ]
  edge [
    source 10
    target 85
    bw 50
    max_bw 50
  ]
  edge [
    source 11
    target 13
    bw 78
    max_bw 78
  ]
  edge [
    source 11
    target 22
    bw 52
    max_bw 52
  ]
  edge [
    source 11
    target 24
    bw 59
    max_bw 59
  ]
  edge [
    source 11
    target 39
    bw 64
    max_bw 64
  ]
  edge [
    source 11
    target 40
    bw 69
    max_bw 69
  ]
  edge [
    source 11
    target 42
    bw 93
    max_bw 93
  ]
  edge [
    source 11
    target 58
    bw 59
    max_bw 59
  ]
  edge [
    source 11
    target 59
    bw 55
    max_bw 55
  ]
  edge [
    source 11
    target 92
    bw 61
    max_bw 61
  ]
  edge [
    source 11
    target 94
    bw 84
    max_bw 84
  ]
  edge [
    source 12
    target 46
    bw 88
    max_bw 88
  ]
  edge [
    source 12
    target 51
    bw 74
    max_bw 74
  ]
  edge [
    source 12
    target 64
    bw 76
    max_bw 76
  ]
  edge [
    source 12
    target 70
    bw 87
    max_bw 87
  ]
  edge [
    source 12
    target 75
    bw 57
    max_bw 57
  ]
  edge [
    source 12
    target 82
    bw 83
    max_bw 83
  ]
  edge [
    source 12
    target 92
    bw 77
    max_bw 77
  ]
  edge [
    source 12
    target 99
    bw 91
    max_bw 91
  ]
  edge [
    source 13
    target 22
    bw 74
    max_bw 74
  ]
  edge [
    source 13
    target 33
    bw 86
    max_bw 86
  ]
  edge [
    source 13
    target 34
    bw 83
    max_bw 83
  ]
  edge [
    source 13
    target 42
    bw 82
    max_bw 82
  ]
  edge [
    source 13
    target 94
    bw 76
    max_bw 76
  ]
  edge [
    source 14
    target 18
    bw 86
    max_bw 86
  ]
  edge [
    source 14
    target 25
    bw 96
    max_bw 96
  ]
  edge [
    source 14
    target 61
    bw 78
    max_bw 78
  ]
  edge [
    source 14
    target 76
    bw 95
    max_bw 95
  ]
  edge [
    source 14
    target 89
    bw 97
    max_bw 97
  ]
  edge [
    source 15
    target 18
    bw 78
    max_bw 78
  ]
  edge [
    source 15
    target 19
    bw 77
    max_bw 77
  ]
  edge [
    source 15
    target 31
    bw 83
    max_bw 83
  ]
  edge [
    source 15
    target 32
    bw 79
    max_bw 79
  ]
  edge [
    source 15
    target 60
    bw 70
    max_bw 70
  ]
  edge [
    source 15
    target 61
    bw 87
    max_bw 87
  ]
  edge [
    source 15
    target 64
    bw 80
    max_bw 80
  ]
  edge [
    source 15
    target 93
    bw 72
    max_bw 72
  ]
  edge [
    source 15
    target 99
    bw 100
    max_bw 100
  ]
  edge [
    source 16
    target 32
    bw 67
    max_bw 67
  ]
  edge [
    source 16
    target 74
    bw 80
    max_bw 80
  ]
  edge [
    source 16
    target 86
    bw 53
    max_bw 53
  ]
  edge [
    source 16
    target 88
    bw 72
    max_bw 72
  ]
  edge [
    source 16
    target 90
    bw 81
    max_bw 81
  ]
  edge [
    source 17
    target 18
    bw 52
    max_bw 52
  ]
  edge [
    source 17
    target 73
    bw 71
    max_bw 71
  ]
  edge [
    source 17
    target 76
    bw 75
    max_bw 75
  ]
  edge [
    source 17
    target 78
    bw 54
    max_bw 54
  ]
  edge [
    source 17
    target 90
    bw 78
    max_bw 78
  ]
  edge [
    source 18
    target 26
    bw 85
    max_bw 85
  ]
  edge [
    source 18
    target 38
    bw 65
    max_bw 65
  ]
  edge [
    source 18
    target 64
    bw 61
    max_bw 61
  ]
  edge [
    source 18
    target 75
    bw 50
    max_bw 50
  ]
  edge [
    source 18
    target 90
    bw 85
    max_bw 85
  ]
  edge [
    source 18
    target 93
    bw 92
    max_bw 92
  ]
  edge [
    source 19
    target 42
    bw 70
    max_bw 70
  ]
  edge [
    source 19
    target 49
    bw 71
    max_bw 71
  ]
  edge [
    source 19
    target 71
    bw 58
    max_bw 58
  ]
  edge [
    source 19
    target 72
    bw 93
    max_bw 93
  ]
  edge [
    source 19
    target 88
    bw 62
    max_bw 62
  ]
  edge [
    source 19
    target 90
    bw 60
    max_bw 60
  ]
  edge [
    source 19
    target 91
    bw 63
    max_bw 63
  ]
  edge [
    source 20
    target 21
    bw 83
    max_bw 83
  ]
  edge [
    source 20
    target 69
    bw 75
    max_bw 75
  ]
  edge [
    source 20
    target 87
    bw 98
    max_bw 98
  ]
  edge [
    source 21
    target 29
    bw 68
    max_bw 68
  ]
  edge [
    source 21
    target 47
    bw 97
    max_bw 97
  ]
  edge [
    source 21
    target 56
    bw 84
    max_bw 84
  ]
  edge [
    source 21
    target 65
    bw 85
    max_bw 85
  ]
  edge [
    source 21
    target 73
    bw 84
    max_bw 84
  ]
  edge [
    source 21
    target 75
    bw 63
    max_bw 63
  ]
  edge [
    source 21
    target 77
    bw 71
    max_bw 71
  ]
  edge [
    source 21
    target 79
    bw 73
    max_bw 73
  ]
  edge [
    source 21
    target 84
    bw 85
    max_bw 85
  ]
  edge [
    source 22
    target 25
    bw 71
    max_bw 71
  ]
  edge [
    source 22
    target 28
    bw 60
    max_bw 60
  ]
  edge [
    source 22
    target 29
    bw 51
    max_bw 51
  ]
  edge [
    source 22
    target 39
    bw 66
    max_bw 66
  ]
  edge [
    source 22
    target 44
    bw 71
    max_bw 71
  ]
  edge [
    source 22
    target 56
    bw 58
    max_bw 58
  ]
  edge [
    source 22
    target 77
    bw 78
    max_bw 78
  ]
  edge [
    source 22
    target 97
    bw 51
    max_bw 51
  ]
  edge [
    source 23
    target 25
    bw 92
    max_bw 92
  ]
  edge [
    source 23
    target 52
    bw 60
    max_bw 60
  ]
  edge [
    source 23
    target 53
    bw 91
    max_bw 91
  ]
  edge [
    source 23
    target 84
    bw 90
    max_bw 90
  ]
  edge [
    source 24
    target 30
    bw 99
    max_bw 99
  ]
  edge [
    source 24
    target 43
    bw 55
    max_bw 55
  ]
  edge [
    source 24
    target 48
    bw 58
    max_bw 58
  ]
  edge [
    source 24
    target 55
    bw 74
    max_bw 74
  ]
  edge [
    source 24
    target 67
    bw 52
    max_bw 52
  ]
  edge [
    source 24
    target 92
    bw 56
    max_bw 56
  ]
  edge [
    source 25
    target 56
    bw 93
    max_bw 93
  ]
  edge [
    source 25
    target 59
    bw 87
    max_bw 87
  ]
  edge [
    source 25
    target 65
    bw 58
    max_bw 58
  ]
  edge [
    source 25
    target 72
    bw 51
    max_bw 51
  ]
  edge [
    source 25
    target 77
    bw 55
    max_bw 55
  ]
  edge [
    source 25
    target 87
    bw 95
    max_bw 95
  ]
  edge [
    source 25
    target 88
    bw 65
    max_bw 65
  ]
  edge [
    source 25
    target 98
    bw 50
    max_bw 50
  ]
  edge [
    source 26
    target 31
    bw 63
    max_bw 63
  ]
  edge [
    source 26
    target 35
    bw 63
    max_bw 63
  ]
  edge [
    source 26
    target 54
    bw 89
    max_bw 89
  ]
  edge [
    source 26
    target 73
    bw 89
    max_bw 89
  ]
  edge [
    source 26
    target 94
    bw 96
    max_bw 96
  ]
  edge [
    source 27
    target 31
    bw 55
    max_bw 55
  ]
  edge [
    source 27
    target 42
    bw 85
    max_bw 85
  ]
  edge [
    source 27
    target 43
    bw 82
    max_bw 82
  ]
  edge [
    source 27
    target 46
    bw 70
    max_bw 70
  ]
  edge [
    source 27
    target 49
    bw 83
    max_bw 83
  ]
  edge [
    source 27
    target 51
    bw 85
    max_bw 85
  ]
  edge [
    source 27
    target 69
    bw 69
    max_bw 69
  ]
  edge [
    source 27
    target 74
    bw 92
    max_bw 92
  ]
  edge [
    source 27
    target 86
    bw 75
    max_bw 75
  ]
  edge [
    source 27
    target 89
    bw 74
    max_bw 74
  ]
  edge [
    source 27
    target 93
    bw 94
    max_bw 94
  ]
  edge [
    source 28
    target 31
    bw 68
    max_bw 68
  ]
  edge [
    source 28
    target 52
    bw 96
    max_bw 96
  ]
  edge [
    source 28
    target 53
    bw 93
    max_bw 93
  ]
  edge [
    source 28
    target 72
    bw 66
    max_bw 66
  ]
  edge [
    source 28
    target 73
    bw 84
    max_bw 84
  ]
  edge [
    source 28
    target 76
    bw 80
    max_bw 80
  ]
  edge [
    source 28
    target 83
    bw 54
    max_bw 54
  ]
  edge [
    source 28
    target 96
    bw 82
    max_bw 82
  ]
  edge [
    source 29
    target 47
    bw 100
    max_bw 100
  ]
  edge [
    source 29
    target 52
    bw 87
    max_bw 87
  ]
  edge [
    source 29
    target 58
    bw 71
    max_bw 71
  ]
  edge [
    source 29
    target 65
    bw 58
    max_bw 58
  ]
  edge [
    source 29
    target 70
    bw 54
    max_bw 54
  ]
  edge [
    source 29
    target 94
    bw 76
    max_bw 76
  ]
  edge [
    source 30
    target 31
    bw 59
    max_bw 59
  ]
  edge [
    source 30
    target 32
    bw 69
    max_bw 69
  ]
  edge [
    source 30
    target 43
    bw 64
    max_bw 64
  ]
  edge [
    source 30
    target 44
    bw 70
    max_bw 70
  ]
  edge [
    source 30
    target 51
    bw 85
    max_bw 85
  ]
  edge [
    source 30
    target 55
    bw 54
    max_bw 54
  ]
  edge [
    source 30
    target 73
    bw 84
    max_bw 84
  ]
  edge [
    source 30
    target 75
    bw 80
    max_bw 80
  ]
  edge [
    source 30
    target 85
    bw 71
    max_bw 71
  ]
  edge [
    source 30
    target 90
    bw 97
    max_bw 97
  ]
  edge [
    source 30
    target 99
    bw 71
    max_bw 71
  ]
  edge [
    source 31
    target 35
    bw 52
    max_bw 52
  ]
  edge [
    source 31
    target 38
    bw 89
    max_bw 89
  ]
  edge [
    source 31
    target 45
    bw 76
    max_bw 76
  ]
  edge [
    source 31
    target 52
    bw 70
    max_bw 70
  ]
  edge [
    source 31
    target 53
    bw 72
    max_bw 72
  ]
  edge [
    source 31
    target 64
    bw 67
    max_bw 67
  ]
  edge [
    source 31
    target 72
    bw 79
    max_bw 79
  ]
  edge [
    source 31
    target 78
    bw 84
    max_bw 84
  ]
  edge [
    source 31
    target 85
    bw 72
    max_bw 72
  ]
  edge [
    source 32
    target 46
    bw 75
    max_bw 75
  ]
  edge [
    source 32
    target 57
    bw 58
    max_bw 58
  ]
  edge [
    source 32
    target 70
    bw 78
    max_bw 78
  ]
  edge [
    source 32
    target 75
    bw 63
    max_bw 63
  ]
  edge [
    source 32
    target 85
    bw 76
    max_bw 76
  ]
  edge [
    source 32
    target 93
    bw 69
    max_bw 69
  ]
  edge [
    source 33
    target 39
    bw 84
    max_bw 84
  ]
  edge [
    source 33
    target 62
    bw 77
    max_bw 77
  ]
  edge [
    source 33
    target 84
    bw 61
    max_bw 61
  ]
  edge [
    source 33
    target 85
    bw 54
    max_bw 54
  ]
  edge [
    source 34
    target 39
    bw 82
    max_bw 82
  ]
  edge [
    source 34
    target 40
    bw 50
    max_bw 50
  ]
  edge [
    source 34
    target 45
    bw 62
    max_bw 62
  ]
  edge [
    source 34
    target 53
    bw 61
    max_bw 61
  ]
  edge [
    source 34
    target 56
    bw 87
    max_bw 87
  ]
  edge [
    source 34
    target 72
    bw 97
    max_bw 97
  ]
  edge [
    source 34
    target 73
    bw 82
    max_bw 82
  ]
  edge [
    source 34
    target 74
    bw 90
    max_bw 90
  ]
  edge [
    source 34
    target 76
    bw 64
    max_bw 64
  ]
  edge [
    source 34
    target 84
    bw 76
    max_bw 76
  ]
  edge [
    source 34
    target 92
    bw 91
    max_bw 91
  ]
  edge [
    source 34
    target 95
    bw 99
    max_bw 99
  ]
  edge [
    source 35
    target 45
    bw 94
    max_bw 94
  ]
  edge [
    source 35
    target 81
    bw 73
    max_bw 73
  ]
  edge [
    source 35
    target 96
    bw 56
    max_bw 56
  ]
  edge [
    source 35
    target 97
    bw 72
    max_bw 72
  ]
  edge [
    source 36
    target 37
    bw 83
    max_bw 83
  ]
  edge [
    source 36
    target 73
    bw 84
    max_bw 84
  ]
  edge [
    source 36
    target 85
    bw 54
    max_bw 54
  ]
  edge [
    source 36
    target 86
    bw 76
    max_bw 76
  ]
  edge [
    source 36
    target 93
    bw 80
    max_bw 80
  ]
  edge [
    source 37
    target 45
    bw 78
    max_bw 78
  ]
  edge [
    source 37
    target 48
    bw 64
    max_bw 64
  ]
  edge [
    source 37
    target 52
    bw 57
    max_bw 57
  ]
  edge [
    source 37
    target 75
    bw 83
    max_bw 83
  ]
  edge [
    source 37
    target 97
    bw 70
    max_bw 70
  ]
  edge [
    source 38
    target 51
    bw 89
    max_bw 89
  ]
  edge [
    source 38
    target 59
    bw 93
    max_bw 93
  ]
  edge [
    source 38
    target 93
    bw 83
    max_bw 83
  ]
  edge [
    source 39
    target 40
    bw 68
    max_bw 68
  ]
  edge [
    source 39
    target 46
    bw 55
    max_bw 55
  ]
  edge [
    source 39
    target 77
    bw 56
    max_bw 56
  ]
  edge [
    source 39
    target 79
    bw 84
    max_bw 84
  ]
  edge [
    source 39
    target 89
    bw 64
    max_bw 64
  ]
  edge [
    source 39
    target 93
    bw 91
    max_bw 91
  ]
  edge [
    source 40
    target 56
    bw 70
    max_bw 70
  ]
  edge [
    source 40
    target 59
    bw 74
    max_bw 74
  ]
  edge [
    source 40
    target 62
    bw 95
    max_bw 95
  ]
  edge [
    source 40
    target 67
    bw 79
    max_bw 79
  ]
  edge [
    source 40
    target 72
    bw 84
    max_bw 84
  ]
  edge [
    source 40
    target 76
    bw 56
    max_bw 56
  ]
  edge [
    source 40
    target 82
    bw 73
    max_bw 73
  ]
  edge [
    source 40
    target 84
    bw 55
    max_bw 55
  ]
  edge [
    source 40
    target 89
    bw 62
    max_bw 62
  ]
  edge [
    source 40
    target 91
    bw 68
    max_bw 68
  ]
  edge [
    source 41
    target 54
    bw 83
    max_bw 83
  ]
  edge [
    source 41
    target 64
    bw 80
    max_bw 80
  ]
  edge [
    source 41
    target 70
    bw 80
    max_bw 80
  ]
  edge [
    source 42
    target 47
    bw 63
    max_bw 63
  ]
  edge [
    source 42
    target 63
    bw 51
    max_bw 51
  ]
  edge [
    source 42
    target 72
    bw 76
    max_bw 76
  ]
  edge [
    source 42
    target 73
    bw 67
    max_bw 67
  ]
  edge [
    source 42
    target 90
    bw 92
    max_bw 92
  ]
  edge [
    source 42
    target 92
    bw 74
    max_bw 74
  ]
  edge [
    source 42
    target 95
    bw 57
    max_bw 57
  ]
  edge [
    source 43
    target 48
    bw 73
    max_bw 73
  ]
  edge [
    source 43
    target 59
    bw 70
    max_bw 70
  ]
  edge [
    source 43
    target 85
    bw 91
    max_bw 91
  ]
  edge [
    source 44
    target 47
    bw 83
    max_bw 83
  ]
  edge [
    source 44
    target 59
    bw 53
    max_bw 53
  ]
  edge [
    source 44
    target 90
    bw 67
    max_bw 67
  ]
  edge [
    source 45
    target 53
    bw 57
    max_bw 57
  ]
  edge [
    source 45
    target 67
    bw 89
    max_bw 89
  ]
  edge [
    source 45
    target 78
    bw 98
    max_bw 98
  ]
  edge [
    source 45
    target 80
    bw 95
    max_bw 95
  ]
  edge [
    source 45
    target 83
    bw 53
    max_bw 53
  ]
  edge [
    source 45
    target 93
    bw 85
    max_bw 85
  ]
  edge [
    source 46
    target 59
    bw 71
    max_bw 71
  ]
  edge [
    source 46
    target 61
    bw 72
    max_bw 72
  ]
  edge [
    source 46
    target 67
    bw 50
    max_bw 50
  ]
  edge [
    source 46
    target 73
    bw 74
    max_bw 74
  ]
  edge [
    source 46
    target 85
    bw 63
    max_bw 63
  ]
  edge [
    source 46
    target 94
    bw 81
    max_bw 81
  ]
  edge [
    source 47
    target 50
    bw 92
    max_bw 92
  ]
  edge [
    source 47
    target 52
    bw 79
    max_bw 79
  ]
  edge [
    source 47
    target 62
    bw 57
    max_bw 57
  ]
  edge [
    source 47
    target 67
    bw 94
    max_bw 94
  ]
  edge [
    source 47
    target 77
    bw 62
    max_bw 62
  ]
  edge [
    source 47
    target 88
    bw 89
    max_bw 89
  ]
  edge [
    source 48
    target 51
    bw 50
    max_bw 50
  ]
  edge [
    source 48
    target 55
    bw 66
    max_bw 66
  ]
  edge [
    source 48
    target 57
    bw 84
    max_bw 84
  ]
  edge [
    source 48
    target 69
    bw 87
    max_bw 87
  ]
  edge [
    source 48
    target 75
    bw 84
    max_bw 84
  ]
  edge [
    source 48
    target 90
    bw 98
    max_bw 98
  ]
  edge [
    source 48
    target 91
    bw 93
    max_bw 93
  ]
  edge [
    source 48
    target 92
    bw 70
    max_bw 70
  ]
  edge [
    source 50
    target 63
    bw 89
    max_bw 89
  ]
  edge [
    source 50
    target 67
    bw 75
    max_bw 75
  ]
  edge [
    source 50
    target 68
    bw 60
    max_bw 60
  ]
  edge [
    source 50
    target 79
    bw 77
    max_bw 77
  ]
  edge [
    source 50
    target 80
    bw 75
    max_bw 75
  ]
  edge [
    source 50
    target 84
    bw 76
    max_bw 76
  ]
  edge [
    source 50
    target 86
    bw 61
    max_bw 61
  ]
  edge [
    source 50
    target 92
    bw 74
    max_bw 74
  ]
  edge [
    source 50
    target 96
    bw 87
    max_bw 87
  ]
  edge [
    source 51
    target 72
    bw 90
    max_bw 90
  ]
  edge [
    source 51
    target 75
    bw 57
    max_bw 57
  ]
  edge [
    source 51
    target 78
    bw 79
    max_bw 79
  ]
  edge [
    source 51
    target 88
    bw 66
    max_bw 66
  ]
  edge [
    source 51
    target 90
    bw 84
    max_bw 84
  ]
  edge [
    source 52
    target 58
    bw 94
    max_bw 94
  ]
  edge [
    source 52
    target 64
    bw 94
    max_bw 94
  ]
  edge [
    source 52
    target 83
    bw 76
    max_bw 76
  ]
  edge [
    source 52
    target 94
    bw 50
    max_bw 50
  ]
  edge [
    source 53
    target 56
    bw 61
    max_bw 61
  ]
  edge [
    source 53
    target 58
    bw 96
    max_bw 96
  ]
  edge [
    source 53
    target 62
    bw 64
    max_bw 64
  ]
  edge [
    source 53
    target 79
    bw 50
    max_bw 50
  ]
  edge [
    source 53
    target 83
    bw 86
    max_bw 86
  ]
  edge [
    source 53
    target 84
    bw 79
    max_bw 79
  ]
  edge [
    source 53
    target 86
    bw 55
    max_bw 55
  ]
  edge [
    source 53
    target 95
    bw 91
    max_bw 91
  ]
  edge [
    source 54
    target 83
    bw 84
    max_bw 84
  ]
  edge [
    source 54
    target 92
    bw 91
    max_bw 91
  ]
  edge [
    source 55
    target 69
    bw 96
    max_bw 96
  ]
  edge [
    source 55
    target 92
    bw 61
    max_bw 61
  ]
  edge [
    source 56
    target 61
    bw 68
    max_bw 68
  ]
  edge [
    source 56
    target 79
    bw 100
    max_bw 100
  ]
  edge [
    source 56
    target 82
    bw 56
    max_bw 56
  ]
  edge [
    source 56
    target 87
    bw 61
    max_bw 61
  ]
  edge [
    source 56
    target 89
    bw 66
    max_bw 66
  ]
  edge [
    source 57
    target 61
    bw 100
    max_bw 100
  ]
  edge [
    source 57
    target 66
    bw 63
    max_bw 63
  ]
  edge [
    source 57
    target 71
    bw 99
    max_bw 99
  ]
  edge [
    source 57
    target 99
    bw 88
    max_bw 88
  ]
  edge [
    source 58
    target 69
    bw 86
    max_bw 86
  ]
  edge [
    source 58
    target 74
    bw 53
    max_bw 53
  ]
  edge [
    source 58
    target 76
    bw 57
    max_bw 57
  ]
  edge [
    source 58
    target 77
    bw 89
    max_bw 89
  ]
  edge [
    source 58
    target 80
    bw 82
    max_bw 82
  ]
  edge [
    source 58
    target 83
    bw 79
    max_bw 79
  ]
  edge [
    source 58
    target 92
    bw 81
    max_bw 81
  ]
  edge [
    source 58
    target 94
    bw 56
    max_bw 56
  ]
  edge [
    source 59
    target 80
    bw 87
    max_bw 87
  ]
  edge [
    source 59
    target 85
    bw 91
    max_bw 91
  ]
  edge [
    source 59
    target 89
    bw 67
    max_bw 67
  ]
  edge [
    source 59
    target 93
    bw 87
    max_bw 87
  ]
  edge [
    source 59
    target 98
    bw 69
    max_bw 69
  ]
  edge [
    source 60
    target 61
    bw 55
    max_bw 55
  ]
  edge [
    source 60
    target 82
    bw 56
    max_bw 56
  ]
  edge [
    source 60
    target 83
    bw 61
    max_bw 61
  ]
  edge [
    source 60
    target 85
    bw 74
    max_bw 74
  ]
  edge [
    source 60
    target 86
    bw 52
    max_bw 52
  ]
  edge [
    source 60
    target 90
    bw 78
    max_bw 78
  ]
  edge [
    source 61
    target 64
    bw 90
    max_bw 90
  ]
  edge [
    source 61
    target 66
    bw 57
    max_bw 57
  ]
  edge [
    source 61
    target 78
    bw 68
    max_bw 68
  ]
  edge [
    source 62
    target 67
    bw 65
    max_bw 65
  ]
  edge [
    source 62
    target 68
    bw 71
    max_bw 71
  ]
  edge [
    source 62
    target 74
    bw 80
    max_bw 80
  ]
  edge [
    source 62
    target 80
    bw 100
    max_bw 100
  ]
  edge [
    source 62
    target 84
    bw 51
    max_bw 51
  ]
  edge [
    source 62
    target 94
    bw 88
    max_bw 88
  ]
  edge [
    source 63
    target 77
    bw 53
    max_bw 53
  ]
  edge [
    source 63
    target 81
    bw 74
    max_bw 74
  ]
  edge [
    source 63
    target 97
    bw 69
    max_bw 69
  ]
  edge [
    source 64
    target 66
    bw 66
    max_bw 66
  ]
  edge [
    source 65
    target 79
    bw 78
    max_bw 78
  ]
  edge [
    source 67
    target 77
    bw 57
    max_bw 57
  ]
  edge [
    source 67
    target 78
    bw 85
    max_bw 85
  ]
  edge [
    source 67
    target 88
    bw 92
    max_bw 92
  ]
  edge [
    source 67
    target 92
    bw 97
    max_bw 97
  ]
  edge [
    source 67
    target 94
    bw 100
    max_bw 100
  ]
  edge [
    source 67
    target 97
    bw 69
    max_bw 69
  ]
  edge [
    source 68
    target 76
    bw 50
    max_bw 50
  ]
  edge [
    source 68
    target 78
    bw 61
    max_bw 61
  ]
  edge [
    source 68
    target 80
    bw 89
    max_bw 89
  ]
  edge [
    source 68
    target 83
    bw 87
    max_bw 87
  ]
  edge [
    source 68
    target 96
    bw 84
    max_bw 84
  ]
  edge [
    source 69
    target 72
    bw 57
    max_bw 57
  ]
  edge [
    source 69
    target 79
    bw 67
    max_bw 67
  ]
  edge [
    source 69
    target 91
    bw 84
    max_bw 84
  ]
  edge [
    source 69
    target 93
    bw 73
    max_bw 73
  ]
  edge [
    source 69
    target 95
    bw 92
    max_bw 92
  ]
  edge [
    source 70
    target 76
    bw 70
    max_bw 70
  ]
  edge [
    source 70
    target 79
    bw 100
    max_bw 100
  ]
  edge [
    source 70
    target 84
    bw 88
    max_bw 88
  ]
  edge [
    source 70
    target 86
    bw 70
    max_bw 70
  ]
  edge [
    source 70
    target 92
    bw 78
    max_bw 78
  ]
  edge [
    source 71
    target 78
    bw 56
    max_bw 56
  ]
  edge [
    source 71
    target 81
    bw 65
    max_bw 65
  ]
  edge [
    source 71
    target 83
    bw 91
    max_bw 91
  ]
  edge [
    source 71
    target 95
    bw 76
    max_bw 76
  ]
  edge [
    source 72
    target 74
    bw 51
    max_bw 51
  ]
  edge [
    source 72
    target 79
    bw 66
    max_bw 66
  ]
  edge [
    source 72
    target 94
    bw 83
    max_bw 83
  ]
  edge [
    source 73
    target 97
    bw 62
    max_bw 62
  ]
  edge [
    source 74
    target 84
    bw 65
    max_bw 65
  ]
  edge [
    source 74
    target 86
    bw 68
    max_bw 68
  ]
  edge [
    source 74
    target 88
    bw 69
    max_bw 69
  ]
  edge [
    source 74
    target 94
    bw 93
    max_bw 93
  ]
  edge [
    source 76
    target 77
    bw 90
    max_bw 90
  ]
  edge [
    source 76
    target 78
    bw 70
    max_bw 70
  ]
  edge [
    source 76
    target 85
    bw 98
    max_bw 98
  ]
  edge [
    source 76
    target 95
    bw 96
    max_bw 96
  ]
  edge [
    source 77
    target 79
    bw 72
    max_bw 72
  ]
  edge [
    source 78
    target 80
    bw 67
    max_bw 67
  ]
  edge [
    source 78
    target 89
    bw 77
    max_bw 77
  ]
  edge [
    source 78
    target 97
    bw 91
    max_bw 91
  ]
  edge [
    source 79
    target 83
    bw 85
    max_bw 85
  ]
  edge [
    source 79
    target 93
    bw 99
    max_bw 99
  ]
  edge [
    source 80
    target 88
    bw 96
    max_bw 96
  ]
  edge [
    source 80
    target 96
    bw 60
    max_bw 60
  ]
  edge [
    source 82
    target 91
    bw 51
    max_bw 51
  ]
  edge [
    source 82
    target 95
    bw 60
    max_bw 60
  ]
  edge [
    source 82
    target 98
    bw 81
    max_bw 81
  ]
  edge [
    source 83
    target 90
    bw 74
    max_bw 74
  ]
  edge [
    source 83
    target 97
    bw 57
    max_bw 57
  ]
  edge [
    source 84
    target 87
    bw 58
    max_bw 58
  ]
  edge [
    source 86
    target 88
    bw 73
    max_bw 73
  ]
  edge [
    source 86
    target 99
    bw 69
    max_bw 69
  ]
  edge [
    source 87
    target 93
    bw 72
    max_bw 72
  ]
  edge [
    source 88
    target 89
    bw 58
    max_bw 58
  ]
  edge [
    source 89
    target 92
    bw 79
    max_bw 79
  ]
  edge [
    source 89
    target 97
    bw 64
    max_bw 64
  ]
  edge [
    source 90
    target 94
    bw 62
    max_bw 62
  ]
  edge [
    source 92
    target 94
    bw 96
    max_bw 96
  ]
  edge [
    source 93
    target 98
    bw 98
    max_bw 98
  ]
]
