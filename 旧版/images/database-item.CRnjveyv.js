import {r as resolveDynamicComponent, o as openBlock, c as createBlock, ae as mergeProps, f as createCommentVNode, b as index$g, H as HTTP_HOST, v as getIsPC, p as processImage, N as getItemIcon, bw as getItemTypeName, q as resolveComponent, w as withCtx, a as createVNode, e as createTextVNode, t as toDisplayString, n as normalizeClass, g as createElementBlock, F as Fragment, h as renderList, Z as normalizeStyle, k as index$i, u as index$q} from "./index-DYB-BZtw.js";
import {_ as __easycom_3} from "./lazy-image.JenCqy9-.js";
import {r as resolveEasycom} from "./uni-app.es.fjQE_VpI.js";
import {_ as __easycom_1$1} from "./uni-icons.CqwQeL__.js";
import {_ as _export_sfc} from "./_plugin-vue_export-helper.BCo6x5W8.js";
import {D as DatabaseLine} from "./database-line.BMsPJCBm.js";
const _sfc_main$1 = {
    inheritAttrs: !1,
    props: {
        game: {
            type: String,
            default: "d4"
        },
        bgPosition: {
            type: String,
            default: ""
        },
        fallbackUrl: {
            type: String,
            default: ""
        }
    }
};
function _sfc_render$1(e, t, i, a, s, o) {
    const l = index$g
      , r = resolveEasycom(resolveDynamicComponent("lazy-image"), __easycom_3);
    return i.bgPosition ? (openBlock(),
    createBlock(l, mergeProps({
        key: 0
    }, e.$attrs, {
        class: ["skill-icon skill-icon--sprite", [`skill-icon--${i.game}`]],
        style: {
            backgroundPosition: i.bgPosition
        }
    }), null, 16, ["class", "style"])) : i.fallbackUrl ? (openBlock(),
    createBlock(r, mergeProps({
        key: 1
    }, e.$attrs, {
        src: i.fallbackUrl,
        mode: "aspectFill",
        class: "skill-icon skill-icon--img"
    }), null, 16, ["src"])) : createCommentVNode("", !0)
}
const __easycom_1 = _export_sfc(_sfc_main$1, [["render", _sfc_render$1], ["__scopeId", "data-v-fac79194"]])
  , cols = 22
  , rows = 20
  , icons = [7099689, 7199608, 17582435, 19873807, 39097082, 44729520, 74547148, 83439307, 106116957, 122135420, 130962716, 131594843, 142120450, 142917427, 146159251, 146175634, 150479992, 166406234, 167629760, 179453850, 185366533, 187554524, 193225823, 193849495, 195728461, 199411772, 200757658, 206312207, 214003632, 238256983, 244480294, 257325815, 260432617, 261928592, 266226442, 275274283, 287013279, 288496840, 295606993, 302691955, 306280496, 313951465, 315796985, 331607739, 333689995, 338166548, 340193677, 342940147, 343690160, 347863029, 353545848, 353880186, 355738272, 367264118, 391072415, 441292488, 446244646, 456796635, 458680120, 462518234, 467020034, 524473312, 537890702, 542812537, 543440774, 543930730, 547330735, 580937795, 597866344, 598845657, 637319997, 638817979, 658829224, 660683193, 663935699, 686684648, 687489707, 700372554, 704167939, 706119458, 706534556, 718084695, 741181077, 742161767, 744033029, 746396387, 750137174, 769067138, 779246405, 824310412, 828581405, 833791648, 835918151, 841332145, 851274538, 867310805, 875227900, 886052643, 898961067, 914686433, 959487912, 963274138, 963405359, 983874568, 1006006396, 1014279793, 1014847393, 1016430048, 1026190482, 1029192303, 1046242558, 1062930714, 1065939741, 1076022204, 1094945979, 1137056403, 1142910994, 1145834007, 1153920890, 1157514517, 1157853967, 1176520382, 1177619171, 1182567971, 1185604044, 1196437418, 1214347041, 1223369082, 1231569317, 1236595861, 1242896448, 1247211689, 1249771554, 1256015583, 1264068485, 1266951540, 1281178120, 1299951619, 1311924934, 1329466172, 1351945218, 1357425399, 1375884437, 1393074912, 1417004774, 1421884793, 1423864768, 1434256090, 1442680028, 1455257110, 1455626004, 1490178539, 1493282523, 1508985014, 1514263133, 1515914741, 1533617475, 1533841030, 1534222278, 1539931079, 1542969974, 1556277706, 1561866532, 1562028099, 1565262918, 1571923641, 1587379851, 1587518667, 1620511740, 1620674625, 1630641762, 1643260497, 1643528245, 1672747461, 1676136447, 1687599785, 1705159566, 1711395052, 1730031292, 1735212522, 1742578310, 1743481334, 1749296362, 1771003917, 1772917457, 1778390952, 1783384410, 1795812775, 1800745969, 1813944211, 1818791500, 1840085604, 1853609998, 1872179382, 1876101767, 1878371654, 1895955344, 1899926082, 1907119310, 1907447993, 1917239879, 1917715779, 1921253938, 1924415126, 1927100127, 1931143625, 1969465491, 1972158944, 1977690456, 1980909659, 1990297850, 1994634449, 2002360620, 2002416328, 2005714594, 2020174388, 2031840440, 2036193161, 2063147248, 2064779860, 2096441689, 2118277567, 2119510002, 2129465824, 2154593671, 2180708071, 2188534045, 2199481972, 2200439282, 2208112296, 2215843391, 2238482307, 2265690523, 2277222871, 2281909844, 2301685477, 2306423942, 2307159530, 2311992589, 2316360295, 2316574748, 2339910827, 2340198233, 2358501978, 2402480109, 2404373593, 2434317759, 2438399663, 2451449073, 2452953735, 2460994705, 2473427407, 2478771237, 2489669816, 2497878058, 2502909985, 2509896079, 2528446673, 2532405507, 2542457481, 2558420214, 2558791083, 2567867606, 2583106860, 2590867783, 2598031404, 2601282180, 2613017133, 2615849514, 2619464679, 2620274440, 2624483768, 2639026498, 2647914824, 2658359495, 2666782071, 2677134938, 2688815990, 2718205048, 2728887595, 2734934320, 2761237404, 2765098979, 2780174111, 2798146585, 2804352630, 2816356316, 2825736727, 2831197174, 2841920196, 2844267581, 2852483453, 2872752988, 2893859777, 2905290015, 2920834280, 2937174745, 3003875885, 3007795371, 3012430126, 3034529424, 3053600066, 3057540394, 3066605190, 3074647649, 3076893419, 3078356075, 3081623323, 3082097118, 3096561380, 3099128485, 3104446884, 3106974408, 3110059165, 3131688435, 3159480441, 3162284554, 3169811489, 3189208735, 3204306676, 3243120679, 3246348700, 3269188177, 3271654496, 3273897890, 3283446701, 3293553708, 3294528623, 3300682957, 3320100639, 3327405852, 3328799720, 3340286619, 3354002559, 3358809279, 3371846932, 3374274781, 3374508764, 3381313342, 3393414993, 3396081931, 3400751470, 3413655459, 3439158182, 3446263887, 3461827257, 3501185050, 3502666833, 3544522700, 3546037569, 3549828161, 3577333848, 3578721249, 3595121784, 3597080939, 3598660560, 3609169654, 3616384966, 3624320072, 3659035354, 3664479412, 3666030594, 3675187692, 3680343924, 3683759362, 3686443240, 3713328411, 3721710535, 3723320970, 3726976296, 3730269316, 3731640435, 3741774242, 3752216763, 3759499301, 3769175811, 3804341086, 3806632672, 3814921826, 3825033762, 3831419091, 3836117954, 3838819186, 3840108468, 3840789304, 3843339215, 3853655021, 3882129668, 3884463898, 3897441388, 3899115645, 3921071145, 3923700034, 3926955448, 3932474169, 3948011034, 3965871508, 3968716431, 3985881759, 3996462973, 3999893968, 4008354426, 4017507106, 4018379697, 4019329760, 4022282752, 4022719148, 4031310682, 4037552102, 4043178673, 4050845547, 4095438116, 4095714092, 4109480457, 4119573290, 4139945836, 4147712587, 4162471874, 4162933847, 4163775100, 4164801007, 4193897029, 4204752281, 4217864944, 4239023902, 4249947077, 4274383807, 4280925177, 4283872183, 4284538946, 4286085851]
  , spriteData = {
    cols: cols,
    rows: rows,
    icons: icons
}
  , COLS = spriteData.cols
  , TOTAL_ROWS = spriteData.rows
  , spriteMap = new Map;
function getSkillSpritePosition(e) {
    if (!spriteMap.has(e))
        return null;
    const t = spriteMap.get(e)
      , i = t % COLS
      , a = Math.floor(t / COLS);
    return `${i / (COLS - 1) * 100}% ${a / (TOTAL_ROWS - 1) * 100}%`
}
function getRankMappedValue(e, t) {
    const i = t - 1;
    return i >= e.length ? e[e.length - 1] : e[i]
}
spriteData.icons.forEach(( (e, t) => spriteMap.set(e, t)));
const _sfc_main = {
    props: {
        item: {
            type: Object,
            default: function(e) {
                return {}
            }
        },
        game: {
            type: String,
            default: "d4"
        },
        type: {
            type: String
        },
        showDetail: Boolean,
        rank: {
            type: Number,
            default: 0
        },
        showMods: {
            type: [Boolean, Array],
            default: !0
        },
        showKeywordDesc: {
            type: Boolean,
            default: !0
        },
        showImage: {
            type: Boolean,
            default: !0
        },
        showEnchantment: {
            type: Boolean,
            default: !0
        },
        selected: Boolean,
        tooltip: Boolean,
        viewType: {
            type: String,
            default: "list"
        }
    },
    data: () => ({
        showDefaultImage: !1,
        checkIcon: `${HTTP_HOST}/data_img/d4/ui/checked.webp`,
        isPC: getIsPC(),
        showSetDesc: !1,
        showMaxSlot: !1
    }),
    components: {
        "database-line": DatabaseLine
    },
    computed: {
        numType() {
            const e = this.item.itemQuality;
            return e ? e > 25 ? "rare" : "magic" : ""
        },
        tooltipText() {
            if ("list" === this.viewType)
                return null;
            if (this.item.tooltip)
                return this.item.tooltip;
            return `${"poe2" === this.game ? "poe2_" : ""}${this.type}:${this.item.key}`
        },
        itemStyle() {
            return "poe2" === this.game && "list" === this.viewType && this.item.bg ? {
                backgroundImage: `url(${HTTP_HOST}/data_img/poe2/skill-bg/${this.item.bg})`,
                backgroundSize: "auto 300px"
            } : {}
        },
        valueMap() {
            const result = {}
              , defaultRank = "tli" === this.game ? 0 : 1
              , rank = this.rank || defaultRank;
            for (let i = 0; i < 10; i++) {
                const key = `value${i}`;
                this.item[key] && ("string" == typeof this.item[key] ? result[key] = Number(eval(this.item[key].replace("{level}", rank)).toFixed(2)) : result[key] = getRankMappedValue(this.item[key], rank));
                const valKey = `val${i}`;
                this.item[valKey] && ("string" == typeof this.item[valKey] ? result[valKey] = Number(eval(this.item[valKey].replace("{level}", rank)).toFixed(2)) : result[valKey] = getRankMappedValue(this.item[valKey], rank))
            }
            return result
        },
        namePrefix() {
            return "vampiricPower" === this.type ? this.$i18n.tm("d4.dataType.vampiricPower") : ""
        },
        name() {
            if ("paragon" === this.type && ["Normal", "Magic"].includes(this.item.quality) && !["Generic_Gate", "StartNode", "Generic_Socket"].some((e => this.item.key.indexOf(e) >= 0))) {
                const e = "Normal" === this.item.quality ? "Common" : this.item.quality;
                return this.$i18n.tm(`d4.paragonNodeType.${e}`)
            }
            return "affix" === this.type ? this.item.prefix + "/" + this.item.suffix : "crafting" === this.type ? "" : "rune" === this.type && this.item.engName !== this.item.name ? `${this.item.name} ${this.item.engName}` : this.item.name
        },
        rankText() {
            if (!this.rank)
                return "";
            if ("tli" === this.game)
                return "talent" === this.type ? "" : `${this.$i18n.tm("d4.ui.common.level")} ${this.rank}`;
            const e = this.item.ranks || 1;
            if (1 === e && 1 === this.rank)
                return "";
            return `${this.$i18n.tm("d4.ui.common.level")} ${this.rank}/${e}`
        },
        titleClass() {
            if (this.item.color)
                return this.item.color;
            if (this.item.isMythic)
                return "d4-color-mythic";
            if ("uniqueItem" === this.type)
                return "d4-color-unique";
            if ("legendary" === this.type)
                return "d4-color-legendary";
            if (this.item.quality) {
                return `d4-color-${"uniqueItem" === this.item.quality ? "unique" : this.item.quality}`.toLowerCase()
            }
            return "heart" === this.type ? "d4-color-heart" : "summon" === this.type ? "d4-color-summon" : "title-default"
        },
        d4SkillSpritePos() {
            return "d4" !== this.game ? null : ["skill", "expertise"].includes(this.type) && getSkillSpritePosition(this.item.icon) || null
        },
        skillIconUrl() {
            return this.item.skillIcon ? processImage(`${HTTP_HOST}/data_img/${this.game}/skill-icon/${this.item.skillIcon}`, 200) : ""
        },
        iconBgUrl() {
            return ["witchPower", "bossPower", "horadricPower", "chaosPerks", "divineGift"].includes(this.type) && this.item.background ? processImage(`${HTTP_HOST}/data_img/${this.game}/ui/${this.type.toLowerCase()}/${this.item.background}.webp`, 200) : ""
        },
        iconUrl() {
            if ("d2r" === this.game)
                return this.item.hd ? processImage(`${HTTP_HOST}/items/${this.item.hd}.png`, 200) : "";
            if ("poe2" === this.game)
                return "item" === this.type || "unique" === this.type ? processImage(`${HTTP_HOST}/data_img/poe2${this.item.icon}`, 200) : "skill" === this.type && "lineage" !== this.item.crafting_level ? processImage(`${HTTP_HOST}/data_img/${this.game}/skill-icon/${this.item.skillIcon}`, 200) : processImage(`${HTTP_HOST}/data_img/poe2/${this.type}/${this.item.icon.toLowerCase()}`, 200);
            if ("tli" === this.game)
                return processImage(`${HTTP_HOST}/data_img/tli/${this.item.icon}.png`, 200);
            if ("legendary" === this.type)
                return processImage(`${HTTP_HOST}/data_img/d4/aspect/${this.item.icon}.webp`, 200);
            if ("paragon" === this.type || "paragonNode" === this.type) {
                const e = this.item.icon;
                return (null == e ? void 0 : e.iconMask) ? processImage(`${HTTP_HOST}/data_img/d4/paragon/${e.iconMask}.webp`, 200) : processImage(`${HTTP_HOST}/data_img/d4/paragon/node_${(null == e ? void 0 : e.foreground) || ""}.webp`, 200)
            }
            if ("uniqueItem" === this.type) {
                const e = this.item.icon ? `${this.item.icon}.webp` : `${this.item.key}_f.png`;
                return processImage(`${HTTP_HOST}/data_img/d4/${this.type}/${e}`, 200)
            }
            if ("glyph" === this.type)
                return processImage(`${HTTP_HOST}/data_img/d4/paragon/node_type_glyph.webp`, 200);
            if ("item" === this.type) {
                if ("uniqueItem" === this.item.quality) {
                    const e = this.item.icon ? `${this.item.icon}.webp` : `${this.item.key}_f.png`;
                    return processImage(`${HTTP_HOST}/data_img/d4/uniqueItem/${e}`, 200)
                }
                return processImage(getItemIcon(this.item.itemType), 200)
            }
            if ("stone" === this.type)
                return processImage(`${HTTP_HOST}/data_img/d4/stone/${this.item.icon}.webp`, 200);
            if ("crafting" === this.type && "d4" === this.game) {
                const e = null != this.item.icon ? this.item.icon : this.item.key;
                return processImage(`${HTTP_HOST}/data_img/d4/crafting/${e}.webp`, 200)
            }
            if (!this.item.key || !this.type)
                return "";
            if ("expertise" === this.type && "Warlock" === this.item.char)
                return "";
            const e = "druid_earth_spike" === this.item.key ? "druid_earth_spike2" : this.item.key
              , t = ["rune", "mercenary", "witchPower", "bossPower", "horadricPower", "chaosPerks", "divineGift", "talisman", "warplan"].includes(this.type) ? "webp" : "png";
            return processImage(`${HTTP_HOST}/data_img/d4/${this.type}/${this.item.icon || e}.${t}`, 200)
        },
        typeName() {
            const e = this.item.charName || this.$i18n.tm("d4.ui.filter.genericClass")
              , t = "enUS" === this.$i18n.locale ? " " : "";
            if ("uniqueItem" === this.type && "d4" === this.game)
                return [e, this.item.equipTypeName].join(" · ");
            if ("legendary" === this.type)
                return this.$i18n.tm(`d4.aspectCategories.${this.item.aspectType}`),
                [this.$i18n.tm(`d4.aspectSource.${this.item.source}`), e, this.item.aspectTypeName].join(" · ");
            if ("mountItem" === this.type)
                return this.$i18n.tm("d4.dataType.mountItem");
            if ("gem" === this.type)
                return this.$i18n.tm("d4.dataType.gem");
            if ("elixir" === this.type)
                return this.$i18n.tm("d4.dataType.elixir");
            if ("crafting" === this.type)
                return this.$i18n.tm("d4.dataType.crafting");
            if ("item" === this.type && "d4" === this.game)
                return getItemTypeName(this.item.quality, this.item.itemType, this.item.itemPower);
            if ("stone" === this.type)
                return this.item.supportType;
            if ("summon" === this.type)
                return this.$i18n.tm("d4.dataType.summon");
            if (["rune", "witchPower", "bossPower", "chaosPerks", "divineGift"].includes(this.type)) {
                const i = this.$i18n.tm(`d4.itemQuality.${this.item.quality}`)
                  , a = this.$i18n.tm(`d4.dataType.${this.type}`);
                return `${"chaosPerks" === this.type ? `${e} · ` : ""}${i}${t}${a}`
            }
            if ("horadricPower" === this.type && "HoradricJewel" === this.item.itemType) {
                return `${this.$i18n.tm(`d4.itemQuality.${this.item.quality}`)}${t}${this.$i18n.tm("d4.dataType.horadricJewel")}`
            }
            if ("talisman" === this.type) {
                return ["Charm" === this.item.type ? this.$i18n.tm("d4.dataType.charm") : this.$i18n.tm("d4.dataType.seal"), this.item.charName || this.$i18n.tm("d4.ui.filter.genericClass")].filter(Boolean).join(" · ")
            }
            return this.item.typeName
        },
        desc() {
            if ("uniqueItem" === this.type && "d4" === this.game)
                return "";
            if ("legendary" === this.type) {
                return [this.$i18n.tm(`d4.aspectCategories.${this.item.aspectType}`)]
            }
            if ("crafting" === this.type)
                return this.item.desc || "";
            if ("expertise" === this.type && 10 === this.rank)
                return [this.item.desc, this.item.bonus];
            if ("talisman" === this.type && (this.item.itemPower || this.item.itemQuality > 0)) {
                const e = [];
                return this.item.itemPower && e.push(`${this.item.itemPower} ${this.$i18n.tm("d4.ui.planner.itemPower")}`),
                this.item.itemQuality > 0 && e.push(`{c_lightgray}${this.$i18n.tm("d4.ui.planner.itemQuality")}: ${this.item.itemQuality}{/c}`),
                e
            }
            if ("item" === this.type && this.item.itemPower) {
                const e = [];
                return e.push(`${this.item.itemPower} ${this.$i18n.tm("d4.ui.planner.itemPower")}`),
                this.item.itemQuality && e.push(`{c_lightgray}${this.item.itemQuality} ${this.$i18n.tm("d4.ui.planner.itemQuality")}{/c}`),
                e
            }
            return "vampiricPower" === this.type ? `${this.$i18n.tm("d4.ui.common.level")} ${this.item.ranks}` : this.item.desc
        },
        descAfter() {
            return "skill" === this.type && this.item.enchantment && !1 !== this.showEnchantment ? this.item.enchantment : "legendary" === this.type || "item" === this.type ? this.item.unlockDesc : "achievement" === this.type ? this.item.desc_list ? this.item.desc_list.map((e => `{c_group}- ${e}{/c}`)).join("") : [] : "gem" === this.type ? `${this.$i18n.tm("d4.ui.common.reqlevel")}: ${this.item.requireLv}` : ""
        },
        mods() {
            if ("skill" === this.type && this.showMods && this.item.mods) {
                return this.item.mods.filter((e => !Array.isArray(this.showMods) || this.showMods.includes(e.engName))).map((e => `{c_label}${e.name}: {/c_label}${e.desc[0]}`))
            }
            return null
        },
        dropBoss() {
            if (this.item.dropBoss) {
                const e = this.item.dropBoss.map((e => `{c_important}${this.$i18n.tm(`d4.dropBoss.${e}`)}{/c}`)).join(", ");
                return `{c_label}${this.$i18n.tm("d4.ui.filter.dropBoss")}{/c}: ${e}`
            }
            return null
        },
        tags() {
            return Array.isArray(this.item.tags) ? "poe2" === this.game && ["item", "unique"].includes(this.type) ? null : "poe2" === this.game && "skill" === this.type && this.item.tags.length > 0 ? this.item.tags.slice(1) : this.item.tags : null
        },
        extra() {
            const e = [];
            if ("poe2" === this.game)
                return this.item.extra && e.push(this.item.extra),
                this.item.nameUS && e.push(this.item.nameUS),
                e.join("\n");
            if ("skill" === this.type && this.item.damageType && e.push(this.item.damageType),
            ["vampiricPower", "stone", "witchPower", "bossPower", "horadricPower", "chaosPerks", "divineGift"].includes(this.type) && this.item.source && e.push(this.item.source),
            "affix" === this.type) {
                const t = this.$i18n.tm("d4.equipType");
                this.item.itemType.forEach((i => {
                    t[i] && e.push(t[i])
                }
                ))
            }
            return this.item.requirements && e.push(this.item.requirements),
            "rune" === this.type && "ConditionRune" === this.item.type && e.push(this.$i18n.tm("d4.tooltip.SocketableConditionRune")),
            "rune" === this.type && "EffectRune" === this.item.type && e.push(this.$i18n.tm("d4.tooltip.SocketableEffectRune")),
            "talisman" === this.type && this.item.levelRequirement && e.push(`${this.$i18n.tm("d4.ui.common.reqlevel")}: ${this.item.levelRequirement}`),
            e.join(" · ")
        },
        arsenalDisplay() {
            const e = this.item.arsenalOptions;
            if (!e || !e.length)
                return null;
            const t = {
                auto: this.$i18n.tm("d4.ui.planner.arsenalAuto"),
                dual: this.$i18n.tm("d4.ui.planner.arsenalDual"),
                blunt: this.$i18n.tm("d4.ui.planner.arsenalBlunt"),
                slash: this.$i18n.tm("d4.ui.planner.arsenalSlash")
            }
              , i = e.length > 1 && this.item.arsenal || e[0];
            return {
                options: e,
                active: i,
                label: t[i] || i
            }
        },
        arsenalGearPreview() {
            const e = this.item.arsenalGearPreview;
            return Array.isArray(e) ? e : []
        },
        keywordsDesc() {
            if (!this.item.filters)
                return [];
            const e = this.$i18n.tm("d4.keywordsDesc");
            return this.item.filters.filter((t => e[t])).map((t => e[t]))
        },
        sectionClass() {
            return "skill" === this.type && void 0 === this.item.active ? "modifiers" : "skill" === this.type && !1 === this.item.active || "mercenary" === this.type && !1 === this.item.active || "expertise" === this.type && "Sorcerer" !== this.item.char ? "passive" : ("paragon" === this.type || "paragonNode" === this.type) && this.item.icon && this.item.icon.background ? this.item.icon.background : "vampiricPower" === this.type ? "round" : "tli" === this.game && "pactSpirit" === this.type ? `tli-item-frame frame-${this.item.quality.toLowerCase()} shadow` : this.item.imageSectionClass ? this.item.imageSectionClass : ""
        },
        imageClass() {
            return "stone" === this.type && this.tooltip ? `d4-frame-${this.item.quality.toLowerCase()}` : ""
        }
    },
    methods: {
        onImageLoad() {
            this.showDefaultImage = !1
        },
        onImageError() {
            this.showDefaultImage = !0
        },
        onTooltipClick() {},
        runeIconUrl: e => e ? processImage(`${HTTP_HOST}/items/misc/${e}.png`, 80) : ""
    }
};
function _sfc_render(e, t, i, a, s, o) {
    const l = index$i
      , r = resolveEasycom(resolveDynamicComponent("lazy-image"), __easycom_3)
      , n = resolveComponent("database-line")
      , c = index$g
      , m = resolveEasycom(resolveDynamicComponent("uni-icons"), __easycom_1$1)
      , p = index$q
      , d = resolveEasycom(resolveDynamicComponent("skill-icon"), __easycom_1);
    return openBlock(),
    createBlock(c, {
        class: normalizeClass(["database-item", {
            [i.type]: !!i.type,
            [i.game]: !!i.game,
            [i.viewType]: !!i.viewType,
            selected: i.selected,
            tooltip: i.tooltip,
            [i.item.quality]: !!i.item.quality,
            Mythic: i.item.isMythic || "Mythic" === i.item.quality
        }]),
        style: normalizeStyle(o.itemStyle),
        ".tooltip": s.isPC ? o.tooltipText : ""
    }, {
        default: withCtx(( () => [createVNode(c, {
            class: "item-left"
        }, {
            default: withCtx(( () => [createVNode(c, {
                class: "item-header"
            }, {
                default: withCtx(( () => [createVNode(c, {
                    class: "item-header-inner"
                }, {
                    default: withCtx(( () => [o.namePrefix ? (openBlock(),
                    createBlock(l, {
                        key: 0,
                        class: "item-title-prefix"
                    }, {
                        default: withCtx(( () => [createTextVNode(toDisplayString(o.namePrefix), 1)])),
                        _: 1
                    })) : createCommentVNode("", !0), o.skillIconUrl ? (openBlock(),
                    createBlock(r, {
                        key: 1,
                        class: "item-skill-icon",
                        src: o.skillIconUrl
                    }, null, 8, ["src"])) : createCommentVNode("", !0), o.name || "crafting" === i.type && i.item.name ? (openBlock(),
                    createBlock(c, {
                        key: 2,
                        class: normalizeClass(["item-title", o.titleClass])
                    }, {
                        default: withCtx(( () => ["crafting" === i.type && i.item.name ? (openBlock(),
                        createBlock(n, {
                            key: 0,
                            text: i.item.name
                        }, null, 8, ["text"])) : o.name ? (openBlock(),
                        createBlock(c, {
                            key: 1
                        }, {
                            default: withCtx(( () => [createTextVNode(toDisplayString(o.name), 1)])),
                            _: 1
                        })) : createCommentVNode("", !0), "list" === i.viewType && "poe2" === i.game && "skill" === i.type && i.item.tags.length > 0 ? (openBlock(),
                        createBlock(c, {
                            key: 2,
                            class: "item-typeline"
                        }, {
                            default: withCtx(( () => [createTextVNode(toDisplayString(i.item.tags[0]), 1)])),
                            _: 1
                        })) : createCommentVNode("", !0), i.item.baseName ? (openBlock(),
                        createBlock(c, {
                            key: 3,
                            class: "base-name"
                        }, {
                            default: withCtx(( () => [createTextVNode(toDisplayString(i.item.baseName), 1)])),
                            _: 1
                        })) : createCommentVNode("", !0)])),
                        _: 1
                    }, 8, ["class"])) : createCommentVNode("", !0), "list" === i.viewType ? (openBlock(),
                    createBlock(c, {
                        key: 3
                    }, {
                        default: withCtx(( () => [o.rankText ? (openBlock(),
                        createBlock(c, {
                            key: 0,
                            class: "item-banner"
                        }, {
                            default: withCtx(( () => [createTextVNode(toDisplayString(o.rankText), 1)])),
                            _: 1
                        })) : createCommentVNode("", !0), o.tags ? (openBlock(),
                        createBlock(c, {
                            key: 1,
                            class: "item-tags"
                        }, {
                            default: withCtx(( () => [(openBlock(!0),
                            createElementBlock(Fragment, null, renderList(o.tags, ( (e, t) => (openBlock(),
                            createBlock(l, {
                                class: "item-filter"
                            }, {
                                default: withCtx(( () => [createTextVNode(toDisplayString(e) + toDisplayString("d4" === i.game || t === o.tags.length - 1 ? "" : ","), 1)])),
                                _: 2
                            }, 1024)))), 256))])),
                            _: 1
                        })) : createCommentVNode("", !0), "d4" === i.game && ["skill", "expertise"].includes(i.type) ? (openBlock(),
                        createBlock(c, {
                            key: 2,
                            class: "item-seperator"
                        })) : createCommentVNode("", !0), o.typeName ? (openBlock(),
                        createBlock(c, {
                            key: 3,
                            class: "item-text item-type"
                        }, {
                            default: withCtx(( () => [createTextVNode(toDisplayString(o.typeName), 1)])),
                            _: 1
                        })) : createCommentVNode("", !0), o.desc ? (openBlock(),
                        createBlock(c, {
                            key: 4,
                            class: "item-desc"
                        }, {
                            default: withCtx(( () => ["d4" === i.game && ["summon"].includes(i.type) ? (openBlock(),
                            createBlock(c, {
                                key: 0,
                                class: "item-seperator left"
                            })) : createCommentVNode("", !0), createVNode(n, {
                                text: o.desc,
                                valueMap: o.valueMap
                            }, null, 8, ["text", "valueMap"])])),
                            _: 1
                        })) : createCommentVNode("", !0), i.item.maxSlot ? (openBlock(),
                        createBlock(c, {
                            key: 5,
                            class: "item-desc item-maxslot"
                        }, {
                            default: withCtx(( () => [createVNode(c, {
                                class: "item-desc-handler",
                                onClick: t[0] || (t[0] = e => s.showMaxSlot = !s.showMaxSlot)
                            }, {
                                default: withCtx(( () => [createVNode(c, null, {
                                    default: withCtx(( () => [createTextVNode("最大孔数：" + toDisplayString(i.item.maxSlot[2]), 1)])),
                                    _: 1
                                }), createVNode(m, {
                                    type: s.showMaxSlot ? "top" : "bottom",
                                    size: "16",
                                    color: ""
                                }, null, 8, ["type"])])),
                                _: 1
                            }), s.showMaxSlot ? (openBlock(),
                            createBlock(c, {
                                key: 0,
                                class: "maxslot-panel"
                            }, {
                                default: withCtx(( () => [createVNode(c, {
                                    class: "maxslot-panel-title"
                                }, {
                                    default: withCtx(( () => [createTextVNode("不同物品等级下的最大孔数")])),
                                    _: 1
                                }), createVNode(c, {
                                    class: "maxslot-list"
                                }, {
                                    default: withCtx(( () => [(openBlock(!0),
                                    createElementBlock(Fragment, null, renderList(i.item.maxSlot, ( (e, t) => (openBlock(),
                                    createBlock(c, {
                                        class: "maxslot-item",
                                        key: t
                                    }, {
                                        default: withCtx(( () => [createVNode(c, {
                                            class: normalizeClass(["maxslot-label", t < 3 ? "maxslot-label-grey" : "maxslot-label-blue"])
                                        }, {
                                            default: withCtx(( () => [createTextVNode(toDisplayString(["1-25", "26-40", "41-99", "1-25", "26-99"][t]), 1)])),
                                            _: 2
                                        }, 1032, ["class"]), createVNode(c, {
                                            class: "maxslot-value"
                                        }, {
                                            default: withCtx(( () => [createTextVNode(toDisplayString(e), 1)])),
                                            _: 2
                                        }, 1024)])),
                                        _: 2
                                    }, 1024)))), 128))])),
                                    _: 1
                                })])),
                                _: 1
                            })) : createCommentVNode("", !0)])),
                            _: 1
                        })) : createCommentVNode("", !0)])),
                        _: 1
                    })) : createCommentVNode("", !0)])),
                    _: 1
                })])),
                _: 1
            }), "list" === i.viewType ? (openBlock(),
            createBlock(c, {
                key: 0,
                class: "item-body"
            }, {
                default: withCtx(( () => [i.item.basicInfo ? (openBlock(),
                createBlock(c, {
                    key: 0,
                    class: "item-info-group"
                }, {
                    default: withCtx(( () => [(openBlock(!0),
                    createElementBlock(Fragment, null, renderList(i.item.basicInfo, (e => (openBlock(),
                    createBlock(c, {
                        class: "item-info"
                    }, {
                        default: withCtx(( () => [e.label ? (openBlock(),
                        createBlock(c, {
                            key: 0,
                            class: "item-info-label"
                        }, {
                            default: withCtx(( () => [createTextVNode(toDisplayString(e.label), 1)])),
                            _: 2
                        }, 1024)) : createCommentVNode("", !0), createVNode(c, {
                            class: "item-info-value"
                        }, {
                            default: withCtx(( () => [createTextVNode(toDisplayString(e.value), 1)])),
                            _: 2
                        }, 1024)])),
                        _: 2
                    }, 1024)))), 256))])),
                    _: 1
                })) : createCommentVNode("", !0), i.item.implict || i.item.armor || i.item.damage ? (openBlock(),
                createBlock(c, {
                    key: 1,
                    class: "item-desc"
                }, {
                    default: withCtx(( () => [createVNode(c, {
                        class: "item-seperator left"
                    }), i.item.damage ? (openBlock(),
                    createBlock(c, {
                        key: 0,
                        class: "item-damage"
                    }, {
                        default: withCtx(( () => [createTextVNode(toDisplayString(i.item.damage), 1)])),
                        _: 1
                    })) : createCommentVNode("", !0), i.item.damageDetails ? (openBlock(),
                    createBlock(c, {
                        key: 1,
                        class: "item-damage-details"
                    }, {
                        default: withCtx(( () => [(openBlock(!0),
                        createElementBlock(Fragment, null, renderList(i.item.damageDetails, (e => (openBlock(),
                        createBlock(c, {
                            class: "item-damage-detail"
                        }, {
                            default: withCtx(( () => [createTextVNode(toDisplayString(e), 1)])),
                            _: 2
                        }, 1024)))), 256))])),
                        _: 1
                    })) : createCommentVNode("", !0), i.item.armor ? (openBlock(),
                    createBlock(c, {
                        key: 2,
                        class: "item-damage"
                    }, {
                        default: withCtx(( () => [createTextVNode(toDisplayString(i.item.armor), 1)])),
                        _: 1
                    })) : createCommentVNode("", !0), createVNode(n, {
                        text: i.item.implict,
                        valueMap: o.valueMap,
                        type: i.type,
                        affix: ""
                    }, null, 8, ["text", "valueMap", "type"])])),
                    _: 1
                })) : createCommentVNode("", !0), i.item.affixesDesc && i.item.affixesDesc.length > 0 ? (openBlock(),
                createBlock(c, {
                    key: 2,
                    class: "item-desc"
                }, {
                    default: withCtx(( () => [createVNode(c, {
                        class: "item-seperator"
                    }), createVNode(n, {
                        text: i.item.affixesDesc,
                        valueMap: o.valueMap,
                        type: i.type,
                        numType: o.numType,
                        affix: ""
                    }, null, 8, ["text", "valueMap", "type", "numType"])])),
                    _: 1
                })) : createCommentVNode("", !0), i.item.setDesc ? (openBlock(),
                createBlock(c, {
                    key: 3,
                    class: "item-desc"
                }, {
                    default: withCtx(( () => [createVNode(c, {
                        class: "item-desc-handler",
                        onClick: t[1] || (t[1] = e => s.showSetDesc = !s.showSetDesc)
                    }, {
                        default: withCtx(( () => [createVNode(c, null, {
                            default: withCtx(( () => [createTextVNode("套装属性")])),
                            _: 1
                        }), createVNode(m, {
                            type: s.showSetDesc ? "top" : "bottom",
                            size: "16",
                            color: ""
                        }, null, 8, ["type"])])),
                        _: 1
                    }), s.showSetDesc ? (openBlock(),
                    createBlock(n, {
                        key: 0,
                        text: i.item.setDesc
                    }, null, 8, ["text"])) : createCommentVNode("", !0)])),
                    _: 1
                })) : createCommentVNode("", !0), o.descAfter ? (openBlock(),
                createBlock(c, {
                    key: 4,
                    class: "item-desc"
                }, {
                    default: withCtx(( () => [createVNode(n, {
                        text: o.descAfter,
                        valueMap: o.valueMap
                    }, null, 8, ["text", "valueMap"])])),
                    _: 1
                })) : createCommentVNode("", !0), i.item.sockets && i.item.sockets.length > 0 ? (openBlock(),
                createBlock(c, {
                    key: 5,
                    class: "item-desc"
                }, {
                    default: withCtx(( () => [(openBlock(!0),
                    createElementBlock(Fragment, null, renderList(i.item.sockets, ( (e, t) => (openBlock(),
                    createBlock(c, {
                        class: "item-socket",
                        key: e.key
                    }, {
                        default: withCtx(( () => [createVNode(c, {
                            class: normalizeClass(["socket", e.socketType])
                        }, {
                            default: withCtx(( () => [createVNode(r, {
                                src: e.icon,
                                class: "socket-icon",
                                mode: "aspectFit"
                            }, null, 8, ["src"])])),
                            _: 2
                        }, 1032, ["class"]), "runeword" === e.type ? (openBlock(),
                        createBlock(c, {
                            key: 0,
                            class: normalizeClass(["socket socket2", e.socketType])
                        }, {
                            default: withCtx(( () => [createVNode(r, {
                                src: e.icon2,
                                class: "socket-icon",
                                mode: "aspectFit"
                            }, null, 8, ["src"])])),
                            _: 2
                        }, 1032, ["class"])) : createCommentVNode("", !0), "runeword" === e.type ? (openBlock(),
                        createBlock(c, {
                            key: 1,
                            class: "socket-link"
                        })) : createCommentVNode("", !0), createVNode(c, null, {
                            default: withCtx(( () => [createVNode(c, {
                                class: normalizeClass(["socket-name", e.type])
                            }, {
                                default: withCtx(( () => [createTextVNode(toDisplayString(e.name), 1)])),
                                _: 2
                            }, 1032, ["class"]), createVNode(n, {
                                text: e.affixesDesc
                            }, null, 8, ["text"])])),
                            _: 2
                        }, 1024)])),
                        _: 2
                    }, 1024)))), 128))])),
                    _: 1
                })) : createCommentVNode("", !0), o.mods && o.mods.length ? (openBlock(),
                createBlock(c, {
                    key: 6,
                    class: "item-mods"
                }, {
                    default: withCtx(( () => [createVNode(c, {
                        class: "item-banner"
                    }, {
                        default: withCtx(( () => [createTextVNode(toDisplayString(e.$tm("d4.tooltip.Modifiers")), 1)])),
                        _: 1
                    }), createVNode(n, {
                        text: o.mods,
                        valueMap: o.valueMap
                    }, null, 8, ["text", "valueMap"])])),
                    _: 1
                })) : createCommentVNode("", !0), i.showKeywordDesc && o.keywordsDesc.length ? (openBlock(),
                createBlock(c, {
                    key: 7,
                    class: "item-keyword"
                }, {
                    default: withCtx(( () => [createVNode(c, {
                        class: "item-seperator left"
                    }), (openBlock(!0),
                    createElementBlock(Fragment, null, renderList(o.keywordsDesc, (e => (openBlock(),
                    createBlock(c, {
                        class: "item-keyword-desc"
                    }, {
                        default: withCtx(( () => [createVNode(n, {
                            text: e
                        }, null, 8, ["text"])])),
                        _: 2
                    }, 1024)))), 256))])),
                    _: 1
                })) : createCommentVNode("", !0), i.item.itemTip ? (openBlock(),
                createBlock(c, {
                    key: 8,
                    class: "item-tip"
                }, {
                    default: withCtx(( () => [createTextVNode(toDisplayString(i.item.itemTip), 1)])),
                    _: 1
                })) : createCommentVNode("", !0), i.item.flavor ? (openBlock(),
                createBlock(c, {
                    key: 9,
                    class: "item-extra item-flavor"
                }, {
                    default: withCtx(( () => [(openBlock(!0),
                    createElementBlock(Fragment, null, renderList(i.item.flavor.split("\\n"), (e => (openBlock(),
                    createBlock(c, null, {
                        default: withCtx(( () => [createVNode(n, {
                            text: e
                        }, null, 8, ["text"])])),
                        _: 2
                    }, 1024)))), 256))])),
                    _: 1
                })) : createCommentVNode("", !0), o.extra ? (openBlock(),
                createBlock(c, {
                    key: 10,
                    class: "item-extra"
                }, {
                    default: withCtx(( () => ["poe2" === i.game ? (openBlock(),
                    createBlock(c, {
                        key: 0,
                        class: "item-seperator"
                    })) : createCommentVNode("", !0), (openBlock(!0),
                    createElementBlock(Fragment, null, renderList(o.extra.split("\n"), (e => (openBlock(),
                    createBlock(c, null, {
                        default: withCtx(( () => [createTextVNode(toDisplayString(e), 1)])),
                        _: 2
                    }, 1024)))), 256))])),
                    _: 1
                })) : createCommentVNode("", !0), o.arsenalDisplay ? (openBlock(),
                createBlock(c, {
                    key: 11,
                    class: "item-arsenal"
                }, {
                    default: withCtx(( () => [createVNode(c, {
                        class: "item-banner"
                    }, {
                        default: withCtx(( () => [createTextVNode(toDisplayString(e.$tm("d4.ui.planner.arsenalSelection")), 1)])),
                        _: 1
                    }), o.arsenalDisplay.options.length > 1 ? (openBlock(),
                    createBlock(c, {
                        key: 0,
                        class: "arsenal-icons"
                    }, {
                        default: withCtx(( () => [(openBlock(!0),
                        createElementBlock(Fragment, null, renderList(o.arsenalDisplay.options, ( (e, t) => (openBlock(),
                        createElementBlock(Fragment, null, [t > 0 ? (openBlock(),
                        createBlock(c, {
                            key: 0,
                            class: "arsenal-sep"
                        })) : createCommentVNode("", !0), createVNode(c, {
                            class: normalizeClass(["arsenal-item", ["arsenal-item--" + e, {
                                "arsenal-item--active": o.arsenalDisplay.active === e
                            }]])
                        }, null, 8, ["class"])], 64)))), 256))])),
                        _: 1
                    })) : createCommentVNode("", !0), createVNode(c, {
                        class: "arsenal-sub-title"
                    }, {
                        default: withCtx(( () => [createTextVNode(toDisplayString(o.arsenalDisplay.label), 1)])),
                        _: 1
                    }), o.arsenalGearPreview.length ? (openBlock(),
                    createBlock(c, {
                        key: 1,
                        class: normalizeClass(["arsenal-equipped", {
                            "arsenal-equipped--dual": 2 === o.arsenalGearPreview.length
                        }])
                    }, {
                        default: withCtx(( () => [(openBlock(!0),
                        createElementBlock(Fragment, null, renderList(o.arsenalGearPreview, ( (e, t) => (openBlock(),
                        createBlock(c, {
                            class: "arsenal-equipped-item",
                            key: t
                        }, {
                            default: withCtx(( () => [createVNode(c, {
                                class: normalizeClass(["arsenal-equipped-frame", e.showType ? `d4-frame-${e.showType}` : ""])
                            }, {
                                default: withCtx(( () => [createVNode(r, {
                                    src: e.imgUrl,
                                    class: "arsenal-equipped-icon",
                                    mode: "aspectFit"
                                }, null, 8, ["src"])])),
                                _: 2
                            }, 1032, ["class"]), createVNode(l, {
                                class: normalizeClass(["arsenal-equipped-name", e.showType ? `d4-color-${e.showType}` : ""])
                            }, {
                                default: withCtx(( () => [createTextVNode(toDisplayString(e.name), 1)])),
                                _: 2
                            }, 1032, ["class"])])),
                            _: 2
                        }, 1024)))), 128))])),
                        _: 1
                    }, 8, ["class"])) : createCommentVNode("", !0)])),
                    _: 1
                })) : createCommentVNode("", !0), "vampiricPower" === i.type ? (openBlock(),
                createBlock(c, {
                    key: 12,
                    class: "item-cost"
                }, {
                    default: withCtx(( () => [createVNode(c, {
                        class: "item-banner"
                    }, {
                        default: withCtx(( () => [createTextVNode(toDisplayString(e.$tm("d4.season2.ActivationCost")), 1)])),
                        _: 1
                    }), createVNode(c, {
                        class: "cost-list"
                    }, {
                        default: withCtx(( () => [(openBlock(!0),
                        createElementBlock(Fragment, null, renderList(i.item.cost, (e => (openBlock(),
                        createBlock(c, {
                            class: "cost-item"
                        }, {
                            default: withCtx(( () => [createTextVNode(toDisplayString(e), 1)])),
                            _: 2
                        }, 1024)))), 256))])),
                        _: 1
                    })])),
                    _: 1
                })) : createCommentVNode("", !0), o.dropBoss ? (openBlock(),
                createBlock(c, {
                    key: 13,
                    class: "mgt-16"
                }, {
                    default: withCtx(( () => [createVNode(c, {
                        class: "item-seperator"
                    }), createVNode(n, {
                        text: o.dropBoss
                    }, null, 8, ["text"])])),
                    _: 1
                })) : createCommentVNode("", !0)])),
                _: 1
            })) : createCommentVNode("", !0)])),
            _: 1
        }), i.showImage && o.iconUrl && "le" !== i.game ? (openBlock(),
        createBlock(c, {
            key: 0,
            class: normalizeClass(["image-section", o.sectionClass])
        }, {
            default: withCtx(( () => [o.iconBgUrl ? (openBlock(),
            createBlock(p, {
                key: 0,
                "fade-show": !1,
                class: "item-image image-background",
                src: o.iconBgUrl,
                mode: "aspectFit"
            }, null, 8, ["src"])) : createCommentVNode("", !0), o.d4SkillSpritePos ? (openBlock(),
            createBlock(d, {
                key: 1,
                class: normalizeClass(["item-image", o.imageClass]),
                game: "d4",
                "bg-position": o.d4SkillSpritePos,
                "fallback-url": o.iconUrl
            }, null, 8, ["class", "bg-position", "fallback-url"])) : o.iconUrl ? (openBlock(),
            createBlock(p, {
                key: 2,
                "fade-show": !1,
                class: normalizeClass(["item-image", o.imageClass]),
                src: o.iconUrl,
                mode: "aspectFit",
                onLoad: o.onImageLoad,
                onError: o.onImageError
            }, null, 8, ["class", "src", "onLoad", "onError"])) : createCommentVNode("", !0), s.showDefaultImage ? (openBlock(),
            createBlock(c, {
                key: 3,
                class: "image-empty-mask"
            }, {
                default: withCtx(( () => [createTextVNode(toDisplayString(e.$tm("d4.ui.common.nopic")), 1)])),
                _: 1
            })) : createCommentVNode("", !0)])),
            _: 1
        }, 8, ["class"])) : createCommentVNode("", !0), i.selected ? (openBlock(),
        createBlock(c, {
            key: 1,
            class: "item-float"
        }, {
            default: withCtx(( () => [createVNode(r, {
                class: "skill-checked",
                src: s.checkIcon
            }, null, 8, ["src"])])),
            _: 1
        })) : createCommentVNode("", !0), "grid" === i.viewType ? (openBlock(),
        createBlock(c, {
            key: 2,
            class: "tooltip-trigger",
            tooltip: o.tooltipText
        }, {
            default: withCtx(( () => [createVNode(m, {
                type: "info",
                class: "trigger-icon",
                size: "24",
                color: ""
            })])),
            _: 1
        }, 8, ["tooltip"])) : createCommentVNode("", !0), createVNode(c, {
            class: "database-item-line"
        }, {
            default: withCtx(( () => [createVNode(c, {
                class: "line-left"
            }), createVNode(c, {
                class: "line-center"
            }), createVNode(c, {
                class: "line-right"
            })])),
            _: 1
        })])),
        _: 1
    }, 40, ["class", "style", ".tooltip"])
}
const DatabaseItem = _export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-452eb2c0"]]);
export {DatabaseItem as D, __easycom_1 as _, getSkillSpritePosition as g};
