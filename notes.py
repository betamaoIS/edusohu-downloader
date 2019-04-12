#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
"""
Created on Sat Apr  6 15:02:27 2019

@author: WxJun
"""

'''
    f41af13ec615423d73b6
            6b37d324516c
    f41af13e b 7d 2451 c


    d376099f553fc34655e5
    d376099f5 3fc 465 e

    33c36b77997d9941f6e5
    33c36b779 7d9 41f e


    1c7bbf5e d6eb473ca653
    1c7bbf5e 5ac74bed
             356ac374be6d
              5 ac 74be d

    07bb60b993fb4c67f6f6
    07bb60b9 ff7c4bf9
            6f6f76c4bf39
             f f7 c4bf 9

    4eccb169e6fe4d661363
    4eccb169 616d4efe
            363166d4ef6e
             6 16 d4ef e

    069b331c991b1148d400
    069b331c9 1b1 48d 0

    315bfdcca1978842a1c3
    315bfdcca 978 42a c

    dc130f41 f6e5473f9393
             3939f3745e6f
    dc130f41  9 9f 745e f

    4c92bfa0b2e58845f666
    4c92bfa0b e58 45f 6

#   d6335e6e v4y42a4w4r52
    d6335e6e  6 92 a47f 2
'''
'''
    abcdefghijklmnopqrstuvwxyz0123456789

#   6fbbb0be x4w44f4p4t35
    6fbbb0be 874f4045

    cad07fcfe 5a1884088c3
    cad07fcfe  a18 408 c

    3f1c6237a 164664f7733 #
    3f1c6237a  646 4f7 3

    3bac9c008 8b2664b4488
    3bac9c008  b26 4b4 8
        if key[-1] in ('3', '6'):
            s1 = key[:8]
            tmp = key[8:][::-1]
            s2 = tmp[1] + tmp[3:5] + tmp[6:10] + tmp[-1]
        else:  # 0 8
            s1 = key[:9]
            s2 = key[9:][1:4] + key[9:][5:8] + key[9:][9]
        return s1 + s2
'''