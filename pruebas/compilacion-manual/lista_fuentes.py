#!/usr/bin/env python3
"""Lista los .cpp que compila PlatformIO para el proyecto (emula common-dependencies.py:
las carpetas de features.ini se excluyen salvo que la feature esté activa)."""
import os, re, sys, subprocess, configparser
P = os.path.abspath(sys.argv[1])
out = subprocess.check_output('g++ -D__MARLIN_DEPS__ -DARDUINO_ARCH_STM32 -DSTM32F4 -DSTM32F4xx -DHAL_STM32 -DPLATFORM_M997_SUPPORT -w -dM -E -x c++ '
                              'buildroot/share/PlatformIO/scripts/common-dependencies.h', shell=True, cwd=P, text=True)
feats = {m.group(1) for m in re.finditer(r'#define (\w+)', out)}
cp = configparser.ConfigParser(strict=False, interpolation=None); cp.optionxform = str
cp.read(os.path.join(P, 'ini/features.ini'))
excl, incl = set(), set()
for feat, val in cp['features'].items():
    for path in re.findall(r'build_src_filter=([^\n]*)', val):
        for sign, p in re.findall(r'([+-])<([^>]+)>', path):
            p = p.rstrip('/')
            if sign == '+':
                (incl if any(re.fullmatch(feat.upper(), n) for n in feats) else excl).add(p)
excl -= incl
# custom_marlin.<FEATURE> = build_src_filter=+<...> de [common_stm32]
st = configparser.ConfigParser(strict=False, interpolation=None); st.optionxform = str
st.read(os.path.join(P, 'ini/stm32-common.ini'))
hal_tft = set()
for k, v in st['common_stm32'].items():
    if k.startswith('custom_marlin.') and k[14:] in feats:
        hal_tft |= set(re.findall(r'\+<(src/HAL/STM32/tft/[^>]+)>', v))
files = []
for root, _, fs in os.walk(os.path.join(P, 'Marlin/src')):
    for f in fs:
        if not f.endswith(('.cpp', '.c')): continue
        rel = os.path.relpath(os.path.join(root, f), os.path.join(P, 'Marlin'))
        if re.match(r'src/(config|tests)/', rel): continue
        if rel.startswith('src/HAL/') and not re.match(r'src/HAL/(STM32|shared)/', rel): continue
        if rel.startswith('src/HAL/STM32/tft/') and rel not in hal_tft: continue
        if any(rel == e or rel.startswith(e + '/') for e in excl): continue
        files.append(rel)
print('\n'.join(sorted(files)))
