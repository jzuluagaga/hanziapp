# -*- coding: utf-8 -*-
"""Content patch — ONLY changes that survive re-adjudication as objective defects."""
import json
E=lambda i,**kw:(str(i),kw)
def entry(no,si,**f):
    o={'no':no,'sense_index':si}; ex=f.pop('examples',None); o.update(f)
    if ex: o['examples']=dict(ex)
    return o
P=[]

# --- headword pinyin: wrong reading / wrong orthography -------------------
P += [entry(157,0,pinyin='piányi'),      # 便 is pián in 便宜
      entry(287,0,pinyin='zhī'),         # classifier 只 = zhī
      entry(40,0, pinyin='dōngxi'),      # "thing" takes neutral xi
      entry(71,2, pinyin='hào'),         # "be fond of" = hào
      entry(153,0,pinyin="nǚ'ér"),       # required syllable apostrophe
      entry(47,0, pinyin='duōshao')]     # interrogative 多少 = duōshao

# --- glosses that contradict the POS or the data --------------------------
P += [entry(63,0,translation_en='to work'),   # EN glosses were swapped
      entry(63,1,translation_en='work'),
      entry(259,0,pos_raw='number-classifier'),
      entry(285,1,meaning_es='verdadero; real')]
for no in (14,24,120,147,227,300):
    P.append(entry(no,0,pos_raw='phrase'))    # six empty pos_raw fields

# --- 44.2 对: "verb: to treat" does not exist; ex0/ex1 duplicated 44.1 ----
P.append(entry(44,2, pos_raw='classifier', translation_en='pair',
  meaning_es='par (clasificador)',
  examples=[E(0, zh='桌子上有一对杯子。', pinyin='zhuō zi shàng yǒu yí duì bēi zi。',
                 es='En la mesa hay un par de tazas.'),
            E(1, zh='树上有一对小鸟。', pinyin='shù shàng yǒu yí duì xiǎo niǎo。',
                 es='En el árbol hay una pareja de pajaritos.')]))

# --- 71.2 好 hào: ex2 could only be read as hǎo -> sense not demonstrated --
P.append(entry(71,2, examples=[
  E(0, pinyin='tā hào yùn dòng。'),
  E(1, pinyin='yé ye hào hē chá。'),
  E(2, zh='他好读书。', pinyin='tā hào dú shū。', es='A él le gusta leer.')]))

# --- sentences that are agrammatical or not modern usage ------------------
P += [
 entry(49,0, examples=[E(0, zh='我住在二楼。', pinyin='wǒ zhù zài èr lóu。',
        es='Vivo en el segundo piso.')]),                    # 二个 -> impossible
 entry(104,0, meaning_es='boca; abertura', examples=[
    E(0, zh='我家门口有一家商店。', pinyin='wǒ jiā mén kǒu yǒu yì jiā shāng diàn。',
        es='A la entrada de mi casa hay una tienda.'),        # 她的口很小
    E(2, zh='这个瓶子的口很小。', pinyin='zhè ge píng zi de kǒu hěn xiǎo。',
        es='La boca de esta botella es muy pequeña.')]),      # 放进口里
 entry(163,0, examples=[E(0, zh='我家门前有一棵大树。',
        pinyin='wǒ jiā mén qián yǒu yì kē dà shù。',
        es='Delante de mi casa hay un árbol grande.')]),      # 我家前 -> 门前
 entry(186,0, examples=[E(0, zh='我们的上课时间是八点。',
        pinyin='wǒ men de shàng kè shí jiān shì bā diǎn。',
        es='Nuestra hora de clase es a las ocho.')]),         # 现在是什么时间
 entry(269,0, examples=[E(1, zh='今天晚上的月亮很亮。',
        pinyin='jīn tiān wǎn shang de yuè liang hěn liàng。',
        es='La luna de esta noche está muy brillante.')]),    # 月 solo != luna
 entry(172,0, examples=[E(2, zh='我的生日是十月一日。',
        pinyin='wǒ de shēng rì shì shí yuè yī rì。',
        es='Mi cumpleaños es el 1 de octubre.')]),            # 请五日假 -> 五天假
 entry(172,1, examples=[E(2, zh='我星期日休息。', pinyin='wǒ xīng qī rì xiū xi。',
        es='Los domingos descanso.')]),                       # 他日 = arcaico
 entry(85,1, examples=[E(2, zh='我在中国住了几年。',
        pinyin='wǒ zài zhōng guó zhù le jǐ nián。',
        es='Viví unos cuantos años en China.')]),             # duplicaba 85.0 ej.1
]

# --- Spanish: objectively wrong, not merely improvable --------------------
P += [
 entry(116,0, examples=[E(0, es='Quiero comprar una prenda nueva.')]),
 entry(242,0, examples=[E(0, es='Compré una prenda de ropa nueva.')]),
 entry(136,0, examples=[E(0, es='Esa es mi mochila.')]),
 entry(266,0, examples=[E(0, es='A algunas personas les gusta el té.')]),
 entry(204,0, examples=[E(0, es='Estas manzanas están muy frescas; las compré esta mañana.')]),
 entry(71,1,  examples=[E(2, es='Hace mucho tiempo que no viene.')]),
 entry(180,1, examples=[E(0, es='A esta oración le falta un carácter.')]),
 entry(214,0, examples=[E(1, es='Vamos a jugar un juego juntos.')]),
 entry(264,0, examples=[E(1, es='Algunos de mis amigos trabajan en Pekín.')]),
 entry(76,1,  examples=[E(0, pinyin='jīn tiān lái le sān shí hào kè rén。',
                            es='Hoy vinieron treinta clientes.')]),
 # --- pinyin repairs that need a hand-written string ---
 entry(147,0, examples=[E(1, pinyin='tā xiào zhe shuō : “ nǐ hǎo ! ”')]),
 entry(124,0, examples=[E(0, pinyin='hái zi men zài wài miàn wán yóu xì。')]),
 entry(172,1, examples=[E(1, pinyin='wǒ men gǎi rì zài jiàn miàn ba。')]),
 entry(181,0, examples=[E(2, pinyin='zhè shì shuí de shǒu jī ?')]),
 entry(105,0, examples=[E(1, pinyin='zhè ge píng guǒ sān kuài qián。')]),
]

merged={}
for o in P:
    k=(o['no'],o['sense_index'])
    if k in merged:
        for kk,vv in o.items():
            if kk in ('no','sense_index'): continue
            if kk=='examples':
                merged[k].setdefault('examples',{})
                for i,f in vv.items(): merged[k]['examples'].setdefault(i,{}).update(f)
            else: merged[k][kk]=vv
    else: merged[k]=dict(o)
out=sorted(merged.values(), key=lambda o:(o['no'],o['sense_index']))
json.dump(out,open('patch_content.json','w'),ensure_ascii=False,indent=1)
print('content patch entries:',len(out))
