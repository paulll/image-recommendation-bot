import asyncio
from models import simplest

async def main():
	likes = {3015481,2986593,3094493,3311460,3167716,2670890,4120224,1711705,3994203,2172953,3064067,1270423,3064064,3289657,888950,3717195,3642793,3380364,3410029,654300,2861155,3640645,2466753,3184141,3304870,3246461,3388202,3068320,3248266,3308531,3308533,3404921,3493898,3512326,3513084,3521775,3525528,3532438,3557264,3668139,3731778,3763958,3782302,3788666,3821621,3837828,3849835,3940001,3889249,3944392,3328522,2900326,3189036,3003114,1972642,3956852,2220301,3425715,1145220,1145224,3099320,3380363,3526646,2550047,3532841,2057518,3519493,1947781,3488090,2980832,1802203,3173877,3064047,3015678,3878056,3878069,3532848,3532847,1477679,1850382,1793349,3514427,3519608,3293758,2758470,2020289,2723322,3361297,3402561,3175048,3526647,2919690,2653105,3363659,2689231,2280141,2705195,658756,2522274,1026897,2989501,2147905,2071899,3355965,3292258,3294151,2459068,2200621,2950256,3306693,3844263,3841836,3826434,3096444,3268712,3031887,3526648,2966429,3467734,3607848,13144,654619,1209578,1103425,368084,1705011,2495207,2724874,2887832,3129858,1727731,1264914,1434703,1903807,2898263,3159732,3133879,3561670,3573264,3574060,3573802,3249410,3521562,3552850,3429997,3561822,3561817,3562601,3569662,3572637,3572652,3507164,3089587,3443323,3487577,2266098,2306823,2227137,3001321,2765114,2756803,2209259,2519770,2912720,2985219,3054858,3259512,3259513,3155710,2157894,1692483,1736042,2146367,2209599,2267255,2146365,1936896,1692485,2765511,2821540,1756240,1445928,2632716,1899740,1740651,1727729,1664615,2295952,2841759,2032329,1832709,3038929,3096395,3146870,3165839,3194195,3096390,3105170,3070494,3031401}
	predicted = await simplest.predict(likes)
	print(predicted)

asyncio.get_event_loop().run_until_complete(main())