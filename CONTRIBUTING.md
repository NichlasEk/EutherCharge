# Bidra

Buggrapporter, dokumentation och små verifierbara analyssteg är välkomna.

Skicka inte firmwaredumpningar, modifierade fullständiga images, nycklar,
serienummer eller material du saknar rätt att distribuera. Ett bra bidrag
innehåller i stället hashvärden, offsetar, förväntade byte och hur resultatet
verifierades.

Innan en pull request:

```sh
python3 -m unittest discover -s tests -v
python3 -m py_compile tools/fwtool.py
```

Var tydlig med evidensnivån: statisk analys, emulering/bänktest och fysisk
KW520-test är separata verifieringssteg.
