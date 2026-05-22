from __future__ import annotations

from io import BytesIO
import base64
import re
from datetime import date
from typing import Iterable

import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps


DEFAULT_EXCLUDED_PRODUCTS = "D600, D460"
DEFAULT_EXCLUDED_ASESOR_CODES = (
    "28005, 34400, 29403, 105-0000, 48400, 08417-001, "
    "11013, 436, 110-G010, Sin codigo, Sin codigo red"
)
DEFAULT_EXCLUDED_ASESOR_PREFIXES = "100-"

MONEY_COLUMNS = {
    "FACTURACION_BRUTA",
    "FACTURACION_ANULADA",
    "FACTURACION_NETA",
    "PRIMA_MEDIA",
}
PERCENT_COLUMNS = {"CHURN_POLIZAS", "CHURN_FACTURACION"}

FORMULA1_BACKGROUND_B64 = """UklGRvYtAABXRUJQVlA4IOotAABQBgGdASpYAlABPm0yl0ckIyetp3JLEbANiWlu3PI9+4lV2o8awjwokE7vTruIgPmsvs2nT1ikl/DP9j/ff6l4mf3X+5/3T/A/87+4e4/ne9F+4HxmumXx/7l+fPTP/n+Bf5h/J/8D1Avxb+bf3f81P7V5zndAW5/1XqBe1vzv/Y/3z/Me+dMj+x9QD/J+lXeRUAP9R6N/9d+3voP+p/2z+BP+c/3j/yfs53IyuP4VqZiAAoQNwg2mPwyL8c1td7t21EDtcsMTV6aUsbN5GMXrdnLdF0del0AXz5sKkHY2qXKGWsQXuG6mIWyFqyuEIPeu35dsoyYSooaiFn0bOGvo8DctxdCHf4L/wsA8bbXRUhDi9v34gLXqxMhgniW3QbeufjlWhayebjKB7Xu1XSh8FaTyKgGLiTcgcDeLJAeqNf4cT0JGX4jCUkwLh0fFScIRy7gkJ+pv9NucAzIzq/YvxMmPl+HBf+aWyzm/qc4pJvYLFpHryU0a94hw1FOZhpW5ZNZCClW0Zfq8ehYM6fE2ri/au3LwBVHHGTEey5EsrJRh1zQbGu3Ra86/xMbXI6w+xk3628V/eRmL8+oDJPGlvQqfCANHQz5Wnx0/VHPRawSunOUtWCPS6vyZNl9xfTDYlnLqVV5ncal2UdKbFCZjUydV9H2mJTt7byxsI76t95k54Af7nuF+uCinMV1sWrdgtAjNvzMArl3xk/cy06Xrsxd1/QhKsTY9OI+XNYD7EOFnyzgZJQb1z9KOSGS0byXxTu/SfWux5NBh554Cm+m1XmM9wpL6fFUOzMAZuytzguPjB4VTgqqjcOc/vvO4AIePuCL/EcLFrwH9ggPxvHT97fC7AuEJ2jOKSz3uQQtSjCtgHsE9dOzNYplIYr9RvecZsfWwRu3/5gbuZoLy3bWU4C2EClS9KZm//o9rXQiF0R0n3VY7FzQx0ivDPJkZw149Uq9kyNEXDIgn4a3wgfteuwCev2ZZdqc/7UQnUGNkSuvTgdV1KZsevnTdAKJRfftlIyYhPtzVbZY/XNNTVe9JSKYL4TBoF08qlKf1Ugb1HThpqzkargoLb8FW9Myh1rOjZI04U/ML4YQU5i6A7ON1dZWRqP9so4g6+jXsLnZYBrvGKehUYS8o5m54fCHmME5Br25HJ6QPDnnZupHr67g/Mu79NkkX+5QXUOKWDdp8jt0c8YSY8J4Y0rGM2gzBj1KDNAaWJuQZ186HvywVHulJETXMTbheH5wJf/wiD4+0UE4Z0wA7mZ7BoBphggA/LCupe0hx/kzP/tcCfc8h+EdY0FTWqRzLG+cSMAokWRP+sk2vD9golhXEKRcLnuuUEiHMizLdc4YP7gSjCStCy2YOhgvc9ZPWmb8ouyv+Csf4fyoi6cSDa7a2ZNZ+Gltf/4zA/kLbNT2gwgYGLFXHhY4BPKzufkaYHbjZea9/cput8H2oQR5BK3EUZtvhMKmeQToORxWyklq1r30EPhak0HEwWqI9trBI3v5Ve6zOJnNm4h/LITDkZr2uwl4A4z7zBUrsxl3/zQlB5OPOyfEkEjBx/YUhLUHFE4c3/Swxe1aorZtuojfw0XHHtcI5E8sB0erolSxksopYqbypSwqn5z4UW5DaOVobCfjeoKWQQ3qgEqL1gq0WpdF8n2FS+GD/wZvk428+Trf/6U58JatrI6MmcVdxlRMmlf1YVdAS5ydA+QcPyLCDQanGN6RFb1SsBGJTp03i43+smGvi/J9sNv9tIZwpMwk1oIh4pKHvFpdYqD1UP7+sHGLFntfJEgMx2lCAKZ8rRStyWCh3h0IA2dIYzLnxYAPB/ZxzKg/CtTUUGlyx5UY7wJNvyJL6ZS715gJIxvIDPNA0BwLsQxdevWeh4hvKtK3xqw18+57N1X13S0gys/PjFuQPF0ldLqcJOfiwfU7Wm91nIXEaZTYS+YrtgDF/ht+mhBzpt+JP2NtOLBG/N0J6DSP0GTV9BXEW8w0NdTqAh0nw4GLVcXmQe83Wq58uM55Bqk+BIJ9I8WEk2vTADiijrCTA3AQ/ytmQk/Lqdruy2UOUd8tAudjFSe1FonNqWo2+w2WaiKyHiTSkFd8TNamX+S8ZCU13CiRm3x/2FsSXddQnDXfCJEU0FIAqzsQ//4pf0t24d+hIlgVzwbL0vijTAfgBTSDX/0lfbeIAHqu4xMCOG6MX7SQcx4zQptnUq8cLWlS9r/+1L1D4sfwkg9Qav/8nV2wnQ79HZA0bTryMgibQA0n86Wla9f+tSpuKULdexYtvnn2rOjI+5BGkE//nI3/9VV4vPmi4vVvCgWgBdKGyp1PErFW9CBoJOwpV34V6EjRklzvVJqB1FZUB6W3aHJ6SzNuSRoY0CxbjclderTlMeeLNb58V/kUU08f9MlZvzk0jcqjbnKy1rw1slbuAz+eeA3rXOj/Ou7cZQImlV5tMpO2mOoUMYdfk39sxuUNJTxEiGSBocaWwYtLeee/CCFMu5fL5X8qLcIkOguPKnmNWXQb8cO5ZBTaA7tEQxZAcZQHjLUZGT+z+U48n0sz19d8kffOhYXrhqM2xn/V72j69jrioXhz8tcHZIgLAg2LiZxS+I0TAz1zBV4xfdGBgPi7PTTWwWVIGfv6N0NCcuxElSfFFM/+uYb2qDC54kPeYUKl0Oyo2dEdIL89q29/+x/+x5zjKhN9zP9pf2VyLzGySgiaNxE8qF+V/9wPJZpSz17Wgc/VPFnTwfqvJiytefJJyyl6qXpOd3S5RQbNPpbPlMRkABPOD28aiK6N6P+oRgfBeiZ+OsXB2P626FQojZ2vrx1oAAP7lTabKZgL4z0IE4A4ku+0xOtBAcYHFNig0vJjJJBV1ClJ2Z+obqand6/8sVoN8hwxxQp/uUn0S24L4KKoZGwEWj+2ZhCHa4ax0n5C1PNYDniR5KQJW9vvWi7zhA36zt4ZI/3S/TWmGX/u64HRnk0qrw6r0ubTrr4psLbyf9ZXPbAnmumN440ovtrGRnbCs8mcbZ0/7WwDcmQTD52tvINSVPVqeA7EoHxeLcefdt5zY3FpmgdOFHTulKDQ0n97084HpVE8xbPmhQZSYSKz5Q8wHj4YKS0P7Ry+TlP17tZEZesrMAhVfv24FwHTDV2wksvXHdAjDPWzxU6IZ0jbhcCdzMDJ/e5W0rbUiapfDa+3Y8s1dPmnteNFZuUIBkJHp8+RdJDzHaLTZv6y/GMtnnXrvS2PFf2bGwWKtExiNWS01gx/O+ihhccawmU3wG6lKwhbm2lk3sEx0bhKUvRJEmssdcuiOeocUlQPcm8//9sZH/U3TwSB4n2LQ8b97t/lnPrNr/lWQUDfiXgyshNUX9UcvQyM2Ir7yKCG+u+OYVH51VS047uA92mfiYxXyVoWBV+s1NytYiWLPTJQOYiUghR1o973qR9oDjobKt3b8UVb7ARajOIHBKXaE+mBSYlP6WE4OLQOG6p94aCIIi1oJ/xbhXYozIc/ytIUNXuePKw9xrPek2Tb1z3+pS/Vgdexvsvo2ml6XNoHcfmsq8RqrfqG2DZvCelDBDpNqtD49ikK6vGBeW0631W+1ezVTbSQvViCSkHwMFK2gA5qQTrx2L/NfuEEoCKgInD9xySVx50UEBi1P9Frl/EQ4qnH7tZzFoxebXjQRQTLsxbSeXpXCoLP8CowyN3e1jWw6ABCVVXt3iyUmuJDeAcxY+4Yo2ECsj/NBDNUNgSuDb1FNgSR/FqbwqPpWpMT/NbtsvF94Tzt2jNjnMZYwrScP03xfjkB6qY2KUD1DDPZgo+l0V3a2HJTJ4LhnpVKL7H5c8B+O9OXIlWZo8SQXppNMdlGCrVVKCODFTsrWTCoxiXcPng+spvHquojjTZeCnpYp7cv7Y6xqDF1kbHf2uh6ZzHAu4VjPu+60BIaeD13nShsXwWEGBcWTPKlEL5o3eyR3vs6pgeA61JJEa6RDhE6pOjyP7wa7w4mlPQkhKQQi/zWkw9GVdZnzyw0W422YTt4YV6j2oFD/8DVMfIJUIfeIINP4Vm+piIhRJ7pytdGMhxr22jjJ0svuSvgBDEV7tWQTC0397gKgzCjz3QPYJsgp2H38J/TBwzY7kqhOHpUt6T6CN/SUdAKKkK25qr85+EJGsuyr0MBmnCrXrRSZpJ9icjHCwOxHUIZMZZLB9+Ht09zpgJYp3ENB8aPQxqmFIjznUHq8IBcEuTdkKWHsF5x8DZYTxBec0BIyp5dRwENfrGZ0ICBhnDpBCc4JO8jaLYyUN55ioYCK0LMEi9c8fwPqUYOmF8Gv213ri6vpoICKFq2dNHSQxZEtMywWFc+XlYmqcLUokgRs+e/+vTOhWcub476FIQ3av51RI1UqATJAr4jrxsG0hQsIuDmLjEvC8mJF6BWJ4iM97MdoW9a1RTKglZCyECpt57TfOCzA3+8P78kfMiiRD3OK+LZGVlBkj6GtashyKAFcXcc7yVvDTXpiiN6O4TzMBXG2pjEePlOvHvNiKrZ9MM+wF/Z7WlzwTlrdW74bBg+0P6Qk33YBq5ODLdBZfpwxLK2h30CYZPngXjkjBiKDGt0DYKMG/+Jaqzyfa6fir8BvCM12nnQwRiCRzE9Sg1cwqyzcgAKZpqC3+8YZpWj0L6pbBHl8tWWEUtfKOtN1YXDQaQnmv6G440/AkJHVanaf84qIoDVVdpci/SECO33MNxRgRkxAV6W8bLACq3uHUELRPO3BHt/9krLIp8Xgzp+7OReBfyj1x5v8baefzoBEs8yV9/kGyDnZOnOuO8ZCEpYLlf7WbB7u0itZQz/WKfXZ1He8A8lOxeKXq2SUoztE7fjT1UmT18o4pDBVgEN9Uuq/gF74O3x2IQxFPDnjQQsWDKaKkwbfQRe/2Q1yaMi/OXlbFrSVq0OVJoA5HFolrXu7qgPOqpeOWmqMmqIIwLKmi75qikeioeaoQRnPBLqkNsAYE+/Tpej08XfdDXOuzWEH49Ho6vXxcifRZXjRtFtfg6s5QIO6oyqJtdsqhMA/QZObZtHirnFtXgCWcUEIQASVBM+9sHZH5CM0t01NXG/7y9HBlVkazekF5fr+S61L9+zbKilszsi/glVmM3NBW+UY9Q7YBCl3Fgj91kt+8e4gCR/1GB8hTnM87ehCxPBHAMM+Uk4xg8v4QL4R8hldA5BkO5HIKd+SuWF/xDG2c6Ylz5YaAJe7hxJKBgXPTLpLpM3S0j+86HpfSTfBTAMaQ1DEZ9WUk7kWiy1Q4sGV0V39FgZejS7yg0snoDAQDqZaaDqahyg2ULQaX0J3oO2J5yKrHXjyUsskIoiRi4F+FAKz9JqmggbFYCpXU8d1Hhzs0WS6gv8inEDgNAxN5jjm8fhlVXc8skhkCRuDzGSJBz8rW1Pc+5mDFKBu+hajv/2j6L/HzDlRVAMfNLjNekVubb+aJkSA2Nct5h0nlLjIbUZXBfelQP3mz1CV4kql050hW0jQgTkem+E9vQD/z/sxfXZHDePtpaBy6gvU1SiITq30nmeX0xhEJMezGnPnk2JV2ctphjPEfhj2uyzgK3LpGukcYaOqUK4CZFJGcqqhePEgoAX6s+1H+4272B6lvJRbc/A5Q5FdnVLHXo7S6fKGGn4UmTIsOWYjvcmgbV8JfLGHZUbjxU5F4P8acmX+a2t9GYvMalpqFkuVCOIQKHdNNDqbruesO5RYFTjfzXXdmh2s80p10RiKhVVfBLVgwAiCF/uqMqJbcqLcVvhH1tbnBpEbU548k0vaFCtMR9MN3VcPz22DBmgZLWOPFYuI6NkfboHLrRXQPwDHLtw9MasSJczV4jQZRpP8DTwxWJ67WzF9RmckpEL1ZmH389OetvjdTD2uwKKCrnZ8vctK+DLug54qLFmrdVc62BOm7LhRn6K+CVWULvxXpnAdLhyO0gv9ka9uvI8gjnOetk09y/vN5sHCXt+IjVygby1FBQ9uoT/ZOKwviuOGt4XYkOMACvMb0H7GSZfrVJCbXodWY+sU5sLHTueZ5jmb6WFq2As5CAbV/0Y1NRj5h1cx5EVYKw6IBHN0vrIVrb34j/0NhQgrLiM0L2PJ7s4vWLklHbhRjCo1a3+hufVaQ3PEjfuJpwA0deDZn5IGnynQhiHlSlkP3Askg2HoQnFrK5BUVqyf4qYuJh+26Sal29qEqlW6p3JF/NzAa/9VUJhEg/RwKdHXitpFeuUIKjjU6vkmCyof0z6yWngKo7c31HuRgGu89FXmXfEZ3IehIO3EfR94h5ajNoSqrl78Es57dZgzpPushEDMUtvGNTky2eFdsrwde6TlkTWwBOH6WxY31gc6bpS6Hc1Jjbyqo3Psu4TVIvBzUEjwCpTjvsVY9OW5ONnsBtf/dLt4+qoGRJEu9fj1BA5zHT/bhe6ViETBiXIQMZxbaiYYeVoZh7Qc0JClM07cCKsHpHPS6p3RnwCT6I/BZXetyDpb6CvLaIMbjJ1AcYn8VpVahkKwvSFM5DaIhd7MJPltIs/55OC3JgYvyTTt3vc4sfQtgyUylk65cYfiOu85DRQWTcbNvcfS7iBpaTlwkB2l/MaResZldf0XnqcV8KJdUCpOofKMMMi3iGHr0RmuMstCQtGhCJYNbiXHy2ccBq5PDz6y8EfI4XLMDXiMEMhsmXadwCvKAekMk/2LxC2WhaJ9wJhq5MX4wxm6hyUVMUt6+cRf79cXSvTBqEiPNDJUw0celnoCWeW6eQ1q+D/hgn7ZHVYJVJNt+ny4XmJa6I1PDVEDCkvbLY3YOE2oXNchVzquP41zU1WS1kjV8S9Q1Eit8qBr5anDkYPpNsIV4WlW40gNQj1aXIFc1izU0SShNHvlzImaU238OO81qjySK4moL+D91LGlog1sAifau9Pn0V+64p4kj3iIKN9ipJjqMMVXo6Ut4U5uT0ggU6hTN+hWafEOuczFsH2Zw1MGshexBST8kZn6ell2QbG1tihYJnTFKTe04dBIDjfvoHaBRNLq64R7jEFhsbXVzHrSs/vPifX/efFsxIJ48JEF6xpw+unN6A0G4X2tloABEkY/6R/GjUL2+REPo20XeKgUDr82kqw7DedNnmu8tLULeJfWVTCGkVA6TzOcKtA4c9/EalY0H+V7xCv8lF+3CQUgeXThhh3g2bZAP5iYzkEOP1JYy2bfll4ythtO1lbTtXYlAOo1jnaozkB4bEbEYkZeocF5qr1BcQqs4oTwNrwkz3jdJAiN7nfPZvl11jKtKVDmIHehvi04aSVKSMUit/ywK+XZjoT9V9xOijObIx/aO0m0kbnGY1kbb+L8YeWgAI3V/jvf1wPfIKz18m7a19gJ7NkcxtJcSrnqsZJgQZ/2iy2wkCAFzM+Z2843OrVDOW/vctTGSZl2vE9/mYDx4ItRrSeo+y003S/QzxHP98Zy/PozVsI7FToR/DYJiXrOr0eTRmidVYEkGZTDlfAh9IDl96NZb3CTHKM2cILcLVB/ElgfzEwadQ95VjM9JM38YWqYBtDLsAUkgYALn6IFTjMUmh4nM/BSyBGRWbuVB3SZuSuMQrEhc5PXejv4uHKKNRogyLygMKcAfVsVAMgS6Uo8cgamHy7s/WhtqfXDXOplW/KAJMLmovLWbBTw4OB+JK1GinT3uKfTDwhG+YEGgkc0t2EjBcGua1ugrDaD1urh3xivvSruR4tO5KykM7nnHhXn2xXqsmMlsnnJaHFDf6EHyJqsoqVLqpWdhG7rD5apUZLEO5CWD+NcPH/2SXORfKqhw5revUpAxfUpNowwSeI5ZKOPa46nXc7zOhlUPKmu4sBHpQNudokGlk3uEH5juuOX8vUuYPrAiYIXrw0cUIA5NJkU0OedKFwhr+HFihRPYL1Ddd1S0Ywr2A6GMnYr0XGz8gwiCW4Q+XdcAexqpwFbeV0XOdlFXwc5rZoKcEywz95lDnDlzCRbBtFf0pQ/fRIILqolsCWRD6hEoifPNA8oG1DCzJUszbfPDlzwCsa/DUdWuPaTbTbeKUc1Kau9FoabYU0FooxI6LWUC+nrPc8d4fA9rKzg4Cr1CLFPBucBVxknqrY2XTTb4K/SZJIGYQxKLh6Gsw8K1fHgj5OxpnlCOVDnvqVgf3YJ4KJz2fK1azazxTfz9E/7Jpksvsd0wqeG54sOJJslrZma4p3OsVfGSSOJwkyG6a01f5owonLxZX9Dw324ZCujDSpqdpCrag+DXg34G6oG8Ky5AhyfUBcl7UOoNyALcWK41Oil00KTPTqZs2sR/eshcPXBZ2E8II1qKLE2H7FiuyhhV/2j0rBK2DKOueSNeDzzNawzhFHwCfMzu7Vy7ijsAdyoEWVhmh7b1ms5HRJk+PcLfS19j6Y7X/63eTbyM24+iQyGKaMcUwMVXm3NwbBMLTqbxGzSjH7fe7F4WXgf9aKvQLjUM1vDLEwfeKa8jWxsDn/t6iq+nOnKHrrTn26V4CPkVCLBAIqOPEVjC11DRB1FRuFRVDPV3nad7nZLfzzEHpkhq1zRx1MXhWzGORfrmr4dJpuroIZUY2MKyufj7Y2txCzYrqQkYOXbzQHijso+MvxyzaKaciPjxKvVEAY9nCDRzuUMdijpcJ6BWZLXa5Pnt0niwhBl3R54BcNHwteXeUDc3zLij93O3hGwcu+5H8bBPYJDb0+s9b6WE2gf6QlNAijNAJ5iS2vGqFLv1IiwJP49pqHGBELE8aOj8xzqaNcfWNg/S5KJ81YKVUuIv+XE0XGTvcMVpNpjQ8GDbpp6CWX7j5WvuyhgOrrWF5eFcOkOBNsyW26sZDcMAQ3Ed8BKNTeXZxTjJsFjKqZnd65GHa/BHajs8vyoUi2vvbiTaB18H1dfN+h1QKHQyKW9XEG94sEpaep8jt0DRnYBNwINv6t1VbPncdJJ9UU0RsUJDbovDl9oYpG2EfMqRhdg92YWewoWAZAozdXlEfRAvjHsS2VtfPfhih9/ruSV8NPZeZ5FvetMWCRMMFICun67KwTr9lF4koDA6fCh7nI5A/ek5HHwEdeONbkdTD94tSkUw6iXaMsr40h+7snBjSAiGnw6jT/ymSLL1qI6ABYQqsi5og3EFPGQogMnk5iNXEnBs4OM1XWcGvcuiAe8hQoLvDExrlpJu19A1V7OPMh+dhQRvUUWyMw0matGtdjPyGFzmXLuZPZfV48tThoSmKG0HdWsumNQthyWCDzbx+i1fRuuuLQChFJYO7PGaG45ZDHWM2YPV30qOki/iHJ/gm+KKD3ta+UBUE/hAww1gOJemXRAeZetiTdqQCg0cdzSVYqW1EKS4isWkdo1cqQlrs+XZiY+rlAJadV40uk3qQoIKZsqP68nvec6xBXThFCNItNfW3XpCCxfKJRf7JSDeSptJnVI10r50Djei5/D2C8rrlKbYpEiERFG0GUs6rCuiDvKG+0xJL2sElmmN7UPjzfg+XgwEkI04QOgfe224fL/cbFhbcyGNKGhUSVDdsXm6BaNhYpQjOUKudpY1l1g/0wpXr1xzeqc8QQDUCj+uCFFJaYV+YBqo83V9ohh32by1UkBROpYNQzzVYlXLff5XCIApK/zY+1FuJKFteo1YX65ZyC7GjnWTnml9JI+HtQSmEgwSBHcTM/BsTbcNqJRv0yC5qA2fISm7hTVqidYOL9BSci9Kl1u9cuyfCI7CMK9y/b9OlhZYjPZLvE2n2EbuqLOdS0Kw/w9I3q0y829iNrSCboGZqjvxSuryuug9D9jXtWULrQE9Siljih8+ETvl+GVKotsnWCCOWJQaTM3iZrmUUcEr42GIQrJtIJWY/8M7B5zoSl7kwvr7NtSsx5iQd7Sh/z5uWLSphQlK2UzaljWj/vvFtf3La8ZA3ts5czjoSuoqNII088tKaijFmmfSdrBR1epYQ1iM0MPG4I//ATjP06tXqqa2kD7/6d/41SL8Qr+7o+6q/Dm4oDCuY5wJAoBL7+DHK1kWNvsLWXnYcu1jfjz8YD3r3GOFWq9rAsSO1e0h4/InRgNEQ1pYYhVIR45aSFRce57OLkRrsVdrgL/sDDXvSl6fw/z1ijN7EZuFmUMcD7n9mdD3EvAGZtTfc3xHtUuGx228WSh+RjAzFELndvbvnQYvj+TYpX3SdL2nN9xWXQVSG/SZWCN0/ExHYSiLj1tViZYixl2zreFXsPPlJ5RbxBpYBSIGvEZJdXmtRJWw6rBQ1fghwlEsqRRA8OkU0JrWPRk8xJtEiomJefSZykHnDFWKjXCU8/9p79L6sQ41P487wHT0rPdpx7nJ3pmAye2S5fRmViVW4N7KzTV2nt10pv+VShz/W60WCcTCmfacvxTfRFLRy8gb94O15FKc9GdBMD21yZDUZD5a0hyZK4kn8anTFOGURLluuo7O6+FPYusD+PTQbcO7QMsyWEscDyiRd69jMRIS21MsRVy71T7W3MEdu7ZMpxL2BjNw6pXuUBSgsX48ulhmvdW0FNdKXVMG5XegpeOTke56kkrj0NqvEO9cko7/7xps0WS6CqEA9vLt75GxVJ+Upvhcw7st5pAa0Q4hnuyCPHFvCydmOuj/sIapD8stC81Bny4xvEb3qCchnzyMV71q/wYpbGjgyb7G/LktNAfqyNUjQi7DTB5n03biOvC4JE1jujA0ysW8j7ACzpU2LbmL/5Ffk10MLQhtIC7EuZMxl6h/h4i4PiTU4JGWZy2/xDz/6T1sHHhlGZqpxBNJqnUTCUWLCYXCyDTyMxV4JEH0h4/7dv54fegFa7hjwtb4n1wgJZBcCJ3ZcltmHCWZUCDx/VpSJloRe9at0/euhNLAvd+ix2QWbR4JyzF2g7qrnfs3DiHQasLMjqKpZNVUHDhi8uXvVaxN538ZYb+9j8bCM33fiwAkVg96SpB6bPHT/0XBkU6LoKx1YZp7GIwicxnrjGEZMU4CFp3WZJ+wfqD9aUOHbjqdNuhLUcTGbrXz6S6eEEjj7y2fAWfARwXbqtzgQwIQnAP72eioWEDMqaySJRIF+QYpCHBTVMSpqd0GSD+QfJgtxYa05vgA9FpZ3gO597YPJSmjxYS1j7fKwLscMBjrVAn4WGEm0Ec2i+uwyNHzxd/96JtCaZ0ObLx3TQR6ylnbK4ISoarcBFeibEeHoSkxj8ijiPGwb59q6U6PwgSCW/IrVvhTnXbL8wVrHZcLwXehKCDPZcduxJSlu/3uX53ZfY2sAS3yswMf966vkXz0n9HyxKb9tjzgbLhO5aGFS8fukO68DhdEyXcAKDY98HSDZiCEpOI2IlONzjkJdYjn1y71d2W7yve+cL1ShbUC1mCJ5VgNGwFuoHKiw9vXLgF7ExcM89Lga/6jPmFFWbSSjBeiceHQYpCmHb1jqMoY4oZnXQ3NatXbFcFeAe9jozi8zJtcNcMtbhU6Xp5JDu5ck21uELU2Et97ZbmlLcqJsnYm+OdKcHavDazNSBNA5bho51Nqq+o6PWqO/Fc2CjqLLbi0NJY8wTpzm5XbiRbc23S0/LgOrh8JOjLnvbu5Hiw9lVAXrsVoIee8BCAoDFNTQOa1GveUyNVUpXjnIejSJ/jN8XVc1Jh4q/sPfLY0QVZQGcIkwAcpwzI0TTY9bEFw+GxWQEUluyXQ/Y7DtwXF9rMatS1SBkohqs7/yL9OVi8IQ8fpNUryvQkEXDNDJSiIlqtYIgT5hJwhE3Xyf3qc6/cMUapgFrcHu9np0i4dVEoGwbybdSz1tALSZPoX30KE7WvZ2KjuT+jK+VOMS8Zgs/zgg5TGcARzfCzN1dU2AraFL8HLqmRewS47OqqeoEbaMBlu59LZrZNN4OZYkC9zIYVuIAaMzOpP7Ro2kK3NBJyNkN4yOWPdVPFcFpS1BOf/RlLyFUFTbiAp+GGn9k5LnB4X/cgCj0qmulQAzR0OeF1O9qj23CxTP2xfag4EKBOGL6zfdG6H/Imy/G+bTTgIEErBZkNXPRRxuR5ex762IiCO+lQPWny8/CmPJGfmChul0IFKNJACqQ8Xau/h6MgZEqFxoOJm7/d4gsNFiJ2vbh2+xxg5loU7tblQnDlXcHEa6T4CXmPB3Qd4wq62FW0b/hfNljofS8OoP3Fn3FPS4+8sWbEnVb87zxpYnwyINhThaAtVEYD2wLdsQW/8YcnWGZ13RBtsgdK/10Zph9Po9cdLT0kVqLpxmF0ImZa+74H3GMVu1JSYS19FvWGSF3OtxX3FS6euquH1dOWex8R9ObiguW/nzcSRTEe5HaFzWRnnr/m3L7QsCLp5IG6Li1wGwm9VZM9yCy/9bdoHGcMLHJImloVvlZE+6opD2/kC99XiZqud8aVO6DlFeYhkY/VIN29TRWXyrKMqf1wpkbIUcScnYPvltHc/DLk8ykSNy6FasZOz9NVxG3fEMxNGODL2Fj5VnqijVYw+1coX+Jh8ZWiMp7Hag9rJCtN9uUJAIevRgfo5gX5kydHTseaog+pZhtcZQ5HRwmGF4agPgRe9xT4enomxglZj8V6ktaSA103V9ohh32a5UTjeffWUPhznOzPNHrlQ805pd/MqKTUd7MRMmlzLL49/CbiWgBZH37KsYx67gimYq4Fk/atKVa6F9PXmuKADZsnrSablM/FLInzdZGNqhSVA4iKOLRmYCON5uS7W7o3bIeOS846UtngHm//3hP0SehivbLWZYE0aq7Sb9Rw5VPmOFavrqbw9zJQ0Pw014vCwgaSiayD62oxy46J6xOPzJxWGiqe5D9MLR/h3ZzgG0A4YV3FetPSv92o2kBBsrAVTEPACT7Tby/k1i74DEqOHQViBOekdlcNL8AyHJJPs+qBnrH2aCKsb6yRDdlZpyArc+Wq2Pwk14B6Ne9DoNzqLa2lkO8Y0aGr0pG1aYlqBU0SvLrfLd+Wyz/VBwOMwOJFMnXL/eZ84P9IcgktISoWWoluOWd/Go5nh3EvHhPq8k96iib7AuagkTPGTva19jnSwkaYkBpQ4VAi+mfWpPBjoj6Rhq1YSnl2SG0wb+fZ/azSxngy02F/VbmCkK5P/wr7xUUIrwGbATyTQU3NiJKv3VhEZ3saELYa3dETM+pdyWm0/kgYrwbrlSVGsGJUvASQMPlzqTVZVZD3KoOq3jBUFOsItj+LOLqf+e2KIXvMA/LlwYDbjNJP5AYeNeDyujuq6qN3+m/7WnN8ete6ef/Ib6vTgc8Q7u8yZhU5A/uIeAVf3cYTyAldsb4hNR5MpWNqldKnk4sDW48EFY8Z0j1jYhTa+PVNa99HySBpy2km/6hSUxNhFJ3/FGiyPKFxcKEAUGFg919sSxPrpTzKZcDGf/LoSoELjwoa46bV1A7oqpbH+nNTm8M9ABEkHmYKWPPeX/NuTqeaLwdquPAZryUSRXgDwJAxJykYbXSL3a36R+PXXt2JtjYBHpS7YnyJFQExBU0PGEdpV1z14Y7ZTlW971kFkjE/HW4G4N1QojQX8x24RcdR6BIHmzY5s6eD2hXB3M2VBgZt+1ghG2KllU25XVw4lYpGQVIwFR3e8SKGO2ZuQ8eEIh0hTK5Q5Nfz+15EkFn5iZaykS4bW0peHVu/gmNK7IZlaxBeDFmPVaFlJw44bvvNCQh8h6E6gX31Mo84h2XIsPR32oW7FPY0ZSdanl5bw7KYEEcVFIHv9OQXsCiqYqg2Ql462HZs5UofuuYvqpc8Gi/I8FvAPAsVbePzmuz1g84kTbyzMKb3G+OBm30BVJqnm3mRNWM8saeLKLIB4xfns80Zp/v2u9UgXQQdXH05eNez4raxIDHM7cvHrbXBgk3KYYiaV/3YBsO2G0HEOV+bTjx62nzF5jG3xHeywls77rU+hYKbAiGOsecBOC+J9+5zJKcUNOmTm4zJUwTETei6/gRYWMh2lN1YA1SwhkAJWRQxvC1bo0ODY18rEfhUYovhVpvW/FB2BRMrKElXYNkQ4K00pa64cNW4z1LyJdugZlrjjiApgkMIfRDvvepXc+JULz1tBwhNJfAVO0OWu7ptFHGzQbtWGzgWO4Atl5LlYRenEo0ZDoMe+KG//9KtXoRuaisotwk8sYOVsGpQTX4mK1SCA23flSuNr3NIo2/Fg5bn2lk3se+4iOz46ng+BDjBKiB9RZauLJvwTv9SJq+461XIFONe1f6MmUhDRAtOM13uxQ1t6aGy3AUw5JW2IVreb112Uq7OtI2inP5Ff6ZHjt2UP4RzNAlqsWIolu+z/ERGDWWQb8CFVzMD5YTEV4cUY0BHkWG1ad9jIY4mnOvM3VvwP34CCRGRPs9icYJ4bJltsX0qQt1Z745koJdLpjwq+rK8RaGM4McBPHYMUoG8d7hxCwtyYLv/05pMdqVAkfHbrCjltMAWqqgEr+FRIAOjmkwMgUi95W6S9COP+NAzIRAE2tqYvEyXKzSaj2Mhx+zdhhQ2cwyOCj2/25RX6n/NMhtFJyV6h5JIuBiHczmKS2UzucRSf0f119R9KeaI769UOQCOzoFKHHFCBe5Z9uY17wx6h0AcFl3DednnSJlrkfHKYuF4HEVje3wz+/fl23nSQvzbpHDOmy/mu82YcD01Q0/RIKiJVwKxjZq7SBG8frxk6DyTIkuV4QmUhIUfupS9btZ6uMD5AuCrZdot6b3HPOKTKM23kdMNLFhX/ZYkYYZHlu+fVd6j/G2e/FlPfb7IC3ZOBAIRzR/rUjPhM+an+96Q1JjsXoiK1FvLyau+Wnlo2WuQbBSsImIxqGkfJJcNfv1tzpkTYLvd+34k9rbOFfj0PZbZUnk8vgdwbNY5WBYUB1SRdMUOLr9hPbcyMPHpYz5EGQQT/337k3Jk/WS4+UQecRChwtco0P59DyNesAFRrSRHVPTadpekd8/3psuH4eHTBV38dixXxO4MUOyQY9Qh9IEvaie5QTaqYfY+NlveBHjyboj9tBw6Tx2jI9dZipuNPYWzdaEi7A0rHXQ2MC9biIlF/avmf+BKKFEdkdLu6VKk2HfAYc7COg/8A6ol350WMQrWzmR4iLYHQUUc+BAmaAguvNnYUGYEwLUZFA+Vob694H29oEv9CSGq9s2s8Hpg7iZxztdpaN5XCpt0Fnc55UYaBGu6hMdJMp3CC12SzWCfbRnTr5Eammwwpooyu07AwLJOpaAsasz4tH6fABufoCDY1AxLtQLm2ra6S3lb3Ldigw+MGPOymiOmGu3F/64BnkBnJGE6Fi/H0Iw2x3slAjfRaZ4uHgeTIQO5+8hb/nxd9DosjqRaAQLqu7GOvqGg15hpdv+gigioMv+3rK016zDFD1YAJ0pQm8JvN5zHzI1enGrqn77L2Oi+wreomoFqMA/9kRfhq0UpLcQS+OhvyC1XFhTY6gBKbTBOEHKtHPCEJayjdJafW6OeoAzNGPd8PhBnY/Uz7SnTx7P89+KNxdoy4oqq5iHVtrmTrD7foDwxbzem0fMS42JvldFIjPmEvZDvLpTzJ+RM1NXy074Vyow+ZjNw3Aht1CvBbfnKbVfTPI4Valb6T/gKvnBYM3EHwrJEFFs1GNDIF62OUrT0/gW50XTCVEkazeBhQ7U+jp9I32DAr8oRQz/qD4mtj/7ZmhcOnjsMMKzsK18t5WlYYTqnGiLHAgilw0W2AWBkSo5c6ck1aR7S9yteywSGwKwENPhQnELphHgkzYiKajcd59lCpdRNUwPWj65/lxNh4s/T1Vxfc2K6kzuHBVGt4ACfKX0CfAGK7qNYAIPERdMq1E8g0IqbPREYmIwOT9AQSswAAAA="""


# ============================================================
# Utilidades generales
# ============================================================

def normalize_column_key(value: object) -> str:
    text = str(value).strip().upper()
    replacements = {"Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ü": "U"}
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def find_column(df: pd.DataFrame, candidates: Iterable[str]) -> str | None:
    normalized = {normalize_column_key(col): col for col in df.columns}
    for candidate in candidates:
        key = normalize_column_key(candidate)
        if key in normalized:
            return normalized[key]
    return None


def require_column(df: pd.DataFrame, candidates: Iterable[str], label: str) -> str:
    col = find_column(df, candidates)
    if col is None:
        raise ValueError(
            f"No encuentro la columna {label}. Columnas leidas: {', '.join(map(str, df.columns))}"
        )
    return col


def parse_spanish_number(value: object) -> float:
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).replace("\xa0", " ").strip()
    text = re.sub(r"[^\d,.\-]", "", text)
    if not text or text in {"-", ",", "."}:
        return 0.0

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(".", "").replace(",", ".")

    try:
        return float(text)
    except ValueError:
        return 0.0


def normalize_text(value: object, default: str = "") -> str:
    if pd.isna(value) or str(value).strip() == "":
        return default
    text = str(value).strip()
    if re.fullmatch(r"\d+\.0", text):
        text = text[:-2]
    return text


def normalize_product(value: object) -> str:
    return normalize_text(value).upper()


def normalize_policy(value: object) -> str:
    return normalize_text(value)


def normalize_reason(value: object) -> str:
    text = normalize_text(value).upper()
    replacements = {"Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ü": "U"}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def split_csv(text: str) -> list[str]:
    return [item.strip() for item in str(text).split(",") if item.strip()]


def parse_date_text(text: str, label: str) -> date:
    raw = str(text).strip()
    try:
        day, month, year = raw.split("/")
        return date(int(year), int(month), int(day))
    except Exception as exc:
        raise ValueError(f"{label} debe tener formato DD/MM/AAAA. Ejemplo: 01/07/2026") from exc


def format_euro(value: float) -> str:
    return f"{float(value):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def format_percent(value: float) -> str:
    return f"{float(value):.2%}".replace(".", ",")


@st.cache_data(show_spinner=False)
def read_excel_uploaded(uploaded_file) -> pd.DataFrame:
    if uploaded_file is None:
        return pd.DataFrame()

    sheets = pd.read_excel(uploaded_file, sheet_name=None, dtype=str)
    frames = []

    for sheet_name, df in sheets.items():
        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]
        df["HOJA_ORIGEN"] = sheet_name
        frames.append(df)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)



def prepare_mapeo_mediadores(df: pd.DataFrame) -> pd.DataFrame:
    """Prepara MAPEO_MEDIADORES para enriquecer el ranking por agente/mediador."""
    if df is None or df.empty:
        return pd.DataFrame(columns=["CODIGO", "NOMBRE_AGENCIA", "PROVINCIA", "RESPONSABLE"])

    cod_col = require_column(df, ("CODIMEDI", "MEDIADOR", "CODIGO", "CODIGO MEDIADOR"), "CODIMEDI")
    nombre_col = find_column(
        df,
        (
            "NOMBCOME",
            "NOMBRE AGENCIA",
            "NOMBRE_AGENCIA",
            "AGENCIA",
            "NOMBRE MEDIADOR",
            "MEDIADOR NOMBRE",
            "NOMBRE",
        ),
    )
    provincia_col = find_column(df, ("PROVINCIA", "POBLACION", "POBLACIÓN", "LOCALIDAD"))
    responsable_col = find_column(df, ("RESPONSABLE", "Responsable"))

    work = df.copy()
    result = pd.DataFrame()
    result["CODIGO"] = work[cod_col].apply(lambda x: normalize_text(x, "Sin mediador"))
    result["NOMBRE_AGENCIA"] = (
        work[nombre_col].apply(lambda x: normalize_text(x, ""))
        if nombre_col
        else ""
    )
    result["PROVINCIA"] = (
        work[provincia_col].apply(lambda x: normalize_text(x, ""))
        if provincia_col
        else ""
    )
    result["RESPONSABLE"] = (
        work[responsable_col].apply(lambda x: normalize_text(x, ""))
        if responsable_col
        else ""
    )

    result = result.drop_duplicates("CODIGO")
    return result


def add_mapeo_to_ranking_agente(ranking: pd.DataFrame, mapeo_df: pd.DataFrame | None) -> pd.DataFrame:
    """Añade nombre de agencia, provincia/población y responsable al ranking por mediador."""
    if ranking.empty or mapeo_df is None or mapeo_df.empty:
        return ranking.copy()

    mapeo = prepare_mapeo_mediadores(mapeo_df)
    if mapeo.empty:
        return ranking.copy()

    result = ranking.copy()
    result = pd.merge(result, mapeo, on="CODIGO", how="left")

    # Si no hay nombre en el mapeo, mantenemos el codigo como nombre.
    result["NOMBRE"] = [
        nombre_agencia if not pd.isna(nombre_agencia) and str(nombre_agencia).strip() else nombre_original
        for nombre_agencia, nombre_original in zip(result["NOMBRE_AGENCIA"], result["NOMBRE"])
    ]

    result["PROVINCIA"] = result["PROVINCIA"].fillna("")
    result["RESPONSABLE"] = result["RESPONSABLE"].fillna("")
    result = result.drop(columns=["NOMBRE_AGENCIA"], errors="ignore")

    ordered = [
        col for col in ["CODIGO", "NOMBRE", "PROVINCIA", "RESPONSABLE"]
        if col in result.columns
    ]
    rest = [col for col in result.columns if col not in ordered]
    return result[ordered + rest]


def available_date_columns(df: pd.DataFrame) -> list[str]:
    priority = [
        "FECHA GRABACION",
        "FECHA_GRABACION",
        "GRABACION",
        "GRABACION_INICIAL",
        "FECGRABA",
        "POLIALTA",
        "POLIEFECT",
        "POLIEFEC",
        "FECHA EFECTO",
        "FECHA ALTA",
    ]

    found: list[str] = []

    for candidate in priority:
        col = find_column(df, (candidate,))
        if col and col not in found:
            found.append(col)

    for col in df.columns:
        key = normalize_column_key(col)
        if (
            "FECHA" in key
            or "FEC" in key
            or "GRABACION" in key
            or key in {"POLIALTA", "POLIEFECT", "POLIEFEC"}
        ) and col not in found:
            found.append(col)

    return found


def get_effect_column(df: pd.DataFrame) -> str:
    # Tope independiente de efecto: SIEMPRE se usa POLIEFECT/POLIEFEC.
    # POLIALTA puede elegirse como fecha de rango, pero NO como tope de efecto.
    return require_column(
        df,
        ("POLIEFECT", "POLIEFEC", "FECHA EFECTO"),
        "POLIEFECT / POLIEFEC / FECHA EFECTO",
    )


# ============================================================
# Preparacion de datos
# ============================================================

def prepare_facturacion_mediador(df: pd.DataFrame, date_column: str) -> pd.DataFrame:
    producto_col = require_column(df, ("PRODUCTO",), "PRODUCTO")
    poliza_col = require_column(df, ("POLIZA",), "POLIZA")
    mediador_col = require_column(df, ("MEDIADOR", "CODIMEDI", "AGENTE"), "MEDIADOR / CODIMEDI")
    prima_col = require_column(df, ("PRIMA NETA", "PRIMA_NETA", "PRIMA NE"), "PRIMA NETA")
    effect_col = get_effect_column(df)

    work = df.copy()
    work["PRODUCTO_NORMALIZADO"] = work[producto_col].apply(normalize_product)
    work["POLIZA_NORMALIZADA"] = work[poliza_col].apply(normalize_policy)
    work["CODIGO"] = work[mediador_col].apply(lambda x: normalize_text(x, "Sin mediador"))
    work["NOMBRE"] = work["CODIGO"]

    # Fecha del rango: la selecciona el usuario.
    work["FECHA_RANKING"] = pd.to_datetime(work[date_column], dayfirst=True, errors="coerce")

    # Tope independiente de efecto: SIEMPRE POLIEFECT/POLIEFEC.
    work["FECHA_EFECTO"] = pd.to_datetime(work[effect_col], dayfirst=True, errors="coerce")

    work["PRIMA_NETA_VALOR"] = work[prima_col].apply(parse_spanish_number)
    return work


def prepare_facturacion_asesor(df: pd.DataFrame, date_column: str) -> pd.DataFrame:
    producto_col = require_column(df, ("PRODUCTO",), "PRODUCTO")
    poliza_col = require_column(df, ("POLIZA",), "POLIZA")
    codigo_col = require_column(
        df,
        ("CODIGO RED COMERCIAL", "CODIGO_RED_COMERCIAL", "CODIGO RED", "CODIGO R"),
        "CODIGO RED COMERCIAL",
    )
    comercial_col = require_column(df, ("COMERCIAL", "ASESOR"), "COMERCIAL")
    prima_col = require_column(df, ("PRIMA NETA", "PRIMA_NETA", "PRIMA NE"), "PRIMA NETA")
    effect_col = get_effect_column(df)

    work = df.copy()
    work["PRODUCTO_NORMALIZADO"] = work[producto_col].apply(normalize_product)
    work["POLIZA_NORMALIZADA"] = work[poliza_col].apply(normalize_policy)
    work["CODIGO"] = work[codigo_col].apply(lambda x: normalize_text(x, "Sin codigo red"))
    work["NOMBRE"] = work[comercial_col].apply(lambda x: normalize_text(x, "Sin asesor"))

    # Fecha del rango: la selecciona el usuario.
    work["FECHA_RANKING"] = pd.to_datetime(work[date_column], dayfirst=True, errors="coerce")

    # Tope independiente de efecto: SIEMPRE POLIEFECT/POLIEFEC.
    work["FECHA_EFECTO"] = pd.to_datetime(work[effect_col], dayfirst=True, errors="coerce")

    work["PRIMA_NETA_VALOR"] = work[prima_col].apply(parse_spanish_number)
    return work


def prepare_anulaciones(df: pd.DataFrame) -> pd.DataFrame:
    producto_col = require_column(df, ("PRODUCTO",), "PRODUCTO")
    poliza_col = require_column(df, ("POLIZA",), "POLIZA")
    prima_col = require_column(df, ("PRIMA NETA", "PRIMA_NETA", "PRIMA NE"), "PRIMA NETA")
    fecha_col = require_column(
        df,
        ("FECHA EMISION", "FECHA_EMISION", "FECHA BAJA", "FECHA ANULACION"),
        "FECHA EMISION",
    )

    mediador_col = find_column(df, ("MEDIADOR", "CODIMEDI", "AGENTE"))
    causa_col = find_column(df, ("CAUSA",))
    motivo_col = find_column(df, ("MOTIVO",))

    work = df.copy()
    work["PRODUCTO_NORMALIZADO"] = work[producto_col].apply(normalize_product)
    work["POLIZA_NORMALIZADA"] = work[poliza_col].apply(normalize_policy)
    work["CODIGO"] = work[mediador_col].apply(lambda x: normalize_text(x, "Sin mediador")) if mediador_col else "Sin mediador"
    work["NOMBRE"] = work["CODIGO"]
    work["FECHA_RANKING"] = pd.to_datetime(work[fecha_col], dayfirst=True, errors="coerce")
    work["PRIMA_NETA_VALOR"] = work[prima_col].apply(parse_spanish_number)
    work["CAUSA_NORMALIZADA"] = work[causa_col].apply(normalize_reason) if causa_col else ""
    work["MOTIVO_NORMALIZADO"] = work[motivo_col].apply(normalize_reason) if motivo_col else ""
    return work


# ============================================================
# Filtros y ranking
# ============================================================

def filter_base(
    df: pd.DataFrame,
    fecha_desde: date,
    fecha_hasta: date,
    excluded_products: set[str],
    fecha_efecto_maxima: date | None,
) -> pd.DataFrame:
    # Primer filtro: rango del ranking con la fecha elegida por el usuario.
    mask = (
        df["FECHA_RANKING"].notna()
        & df["FECHA_RANKING"].dt.date.ge(fecha_desde)
        & df["FECHA_RANKING"].dt.date.le(fecha_hasta)
        & ~df["PRODUCTO_NORMALIZADO"].isin(excluded_products)
    )

    # Segundo filtro: tope independiente de efecto con POLIEFECT/POLIEFEC.
    if fecha_efecto_maxima is not None:
        mask = (
            mask
            & df["FECHA_EFECTO"].notna()
            & df["FECHA_EFECTO"].dt.date.le(fecha_efecto_maxima)
        )

    return df[mask].copy()


def filter_anulaciones(
    df: pd.DataFrame,
    fecha_desde: date,
    fecha_hasta: date,
    excluded_products: set[str],
    excluir_defuncion_siniestro: bool,
) -> pd.DataFrame:
    mask = (
        df["FECHA_RANKING"].notna()
        & df["FECHA_RANKING"].dt.date.ge(fecha_desde)
        & df["FECHA_RANKING"].dt.date.le(fecha_hasta)
        & ~df["PRODUCTO_NORMALIZADO"].isin(excluded_products)
    )

    if excluir_defuncion_siniestro:
        causa = (
            df["CAUSA_NORMALIZADA"].astype(str)
            if "CAUSA_NORMALIZADA" in df.columns
            else pd.Series("", index=df.index)
        )
        motivo = (
            df["MOTIVO_NORMALIZADO"].astype(str)
            if "MOTIVO_NORMALIZADO" in df.columns
            else pd.Series("", index=df.index)
        )
        excluded_reason = (
            causa.str.startswith("DEFUNCION", na=False)
            | causa.str.startswith("INDIVIDUAL POR SINIESTRO", na=False)
            | motivo.str.startswith("DEFUNCION", na=False)
            | motivo.str.startswith("SINIESTRO TOTAL", na=False)
        )
        mask = mask & ~excluded_reason

    return df[mask].copy()


def exclude_asesor_codes(df: pd.DataFrame, exact_codes: list[str], prefixes: list[str]) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    work = df.copy()
    codigo = work["CODIGO"].fillna("").astype(str).str.strip()
    nombre = work["NOMBRE"].fillna("").astype(str).str.strip().str.upper()
    exact = {str(c).strip() for c in exact_codes if str(c).strip()}

    mask = codigo.isin(exact) | nombre.eq("SIN ASESOR") | codigo.eq("")
    for prefix in prefixes:
        if prefix.strip():
            mask = mask | codigo.str.startswith(prefix.strip(), na=False)

    return work[~mask].copy()


def apply_effect_filter_to_annulment_lookup(
    lookup: pd.DataFrame,
    fecha_efecto_maxima: date | None,
) -> pd.DataFrame:
    """Aplica a las bajas el mismo tope de POLIEFECT usado para las altas."""
    if fecha_efecto_maxima is None or lookup.empty:
        return lookup

    return lookup[
        lookup["FECHA_EFECTO"].notna()
        & lookup["FECHA_EFECTO"].dt.date.le(fecha_efecto_maxima)
    ].copy()


def aggregate_detail(df: pd.DataFrame, amount_name: str, count_name: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["CODIGO", "NOMBRE", amount_name, count_name])

    return (
        df.groupby(["CODIGO", "NOMBRE"], dropna=False)
        .agg(
            **{
                amount_name: ("PRIMA_NETA_VALOR", "sum"),
                count_name: ("POLIZA_NORMALIZADA", "nunique"),
            }
        )
        .reset_index()
    )


def build_ranking(
    facturacion_df: pd.DataFrame,
    anulaciones_df: pd.DataFrame,
    facturacion_asesor_df: pd.DataFrame | None,
    mapeo_df: pd.DataFrame | None,
    ranking_por: str,
    date_column: str,
    fecha_desde: date,
    fecha_hasta: date,
    excluded_products: list[str],
    fecha_efecto_maxima: date | None,
    metric: str,
    excluir_defuncion_siniestro: bool,
    solo_bajas_altas_mismo_anio: bool,
    excluded_asesor_codes: list[str],
    excluded_asesor_prefixes: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    excluded_products_set = {normalize_product(p) for p in excluded_products}

    if ranking_por == "Asesor / comercial":
        if facturacion_asesor_df is None or facturacion_asesor_df.empty:
            raise ValueError("Para ranking por asesor necesitas subir FACTURACION_DECESOS_ASESOR.")
        altas_prepared = prepare_facturacion_asesor(facturacion_asesor_df, date_column)
    else:
        altas_prepared = prepare_facturacion_mediador(facturacion_df, date_column)

    anulaciones_prepared = prepare_anulaciones(anulaciones_df)

    # ALTAS:
    # 1) rango con la fecha seleccionada
    # 2) opcionalmente tope máximo con POLIEFECT/POLIEFEC
    altas_detail = filter_base(
        altas_prepared,
        fecha_desde,
        fecha_hasta,
        excluded_products_set,
        fecha_efecto_maxima,
    )

    # ANULACIONES:
    # por defecto se filtran por FECHA EMISION dentro del mismo periodo.
    anulaciones_detail_base = filter_anulaciones(
        anulaciones_prepared,
        fecha_desde,
        fecha_hasta,
        excluded_products_set,
        excluir_defuncion_siniestro,
    )

    if ranking_por == "Asesor / comercial":
        # Para imputar bajas a asesor cruzamos por POLIZA contra FACTURACION_DECESOS_ASESOR.
        lookup = altas_prepared[["POLIZA_NORMALIZADA", "CODIGO", "NOMBRE", "FECHA_EFECTO"]].copy()

        if solo_bajas_altas_mismo_anio:
            lookup = lookup[lookup["FECHA_EFECTO"].dt.year == fecha_hasta.year]

        lookup = apply_effect_filter_to_annulment_lookup(lookup, fecha_efecto_maxima)
        lookup = lookup.drop_duplicates("POLIZA_NORMALIZADA")

        anulaciones_detail = pd.merge(
            anulaciones_detail_base.drop(columns=["CODIGO", "NOMBRE"], errors="ignore"),
            lookup[["POLIZA_NORMALIZADA", "CODIGO", "NOMBRE"]],
            on="POLIZA_NORMALIZADA",
            how="inner",
        )

        altas_detail = exclude_asesor_codes(
            altas_detail,
            excluded_asesor_codes,
            excluded_asesor_prefixes,
        )
        anulaciones_detail = exclude_asesor_codes(
            anulaciones_detail,
            excluded_asesor_codes,
            excluded_asesor_prefixes,
        )

    else:
        # Para ranking por agente/mediador, si hay tope de efecto, las bajas tambien
        # se restringen a polizas cuyo POLIEFECT/POLIEFEC cumple ese tope.
        if fecha_efecto_maxima is not None:
            lookup = altas_prepared[["POLIZA_NORMALIZADA", "FECHA_EFECTO"]].copy()
            lookup = apply_effect_filter_to_annulment_lookup(lookup, fecha_efecto_maxima)
            lookup = lookup.drop_duplicates("POLIZA_NORMALIZADA")

            anulaciones_detail = pd.merge(
                anulaciones_detail_base,
                lookup[["POLIZA_NORMALIZADA"]],
                on="POLIZA_NORMALIZADA",
                how="inner",
            )
        else:
            anulaciones_detail = anulaciones_detail_base

    altas = aggregate_detail(altas_detail, "FACTURACION_BRUTA", "POLIZAS_GRABADAS")
    anulaciones = aggregate_detail(anulaciones_detail, "FACTURACION_ANULADA", "POLIZAS_ANULADAS")

    ranking = pd.merge(altas, anulaciones, on=["CODIGO", "NOMBRE"], how="outer")

    if ranking.empty:
        return ranking, altas_detail, anulaciones_detail

    for col in ["FACTURACION_BRUTA", "POLIZAS_GRABADAS", "FACTURACION_ANULADA", "POLIZAS_ANULADAS"]:
        ranking[col] = pd.to_numeric(ranking[col], errors="coerce").fillna(0)

    ranking["FACTURACION_NETA"] = ranking["FACTURACION_BRUTA"] - ranking["FACTURACION_ANULADA"]
    ranking["POLIZAS_NETAS"] = ranking["POLIZAS_GRABADAS"] - ranking["POLIZAS_ANULADAS"]
    ranking["PRIMA_MEDIA"] = [
        fact / pol if pol else 0.0
        for fact, pol in zip(ranking["FACTURACION_NETA"], ranking["POLIZAS_NETAS"])
    ]
    ranking["CHURN_POLIZAS"] = [
        baja / alta if alta else 0.0
        for baja, alta in zip(ranking["POLIZAS_ANULADAS"], ranking["POLIZAS_GRABADAS"])
    ]
    ranking["CHURN_FACTURACION"] = [
        baja / alta if alta else 0.0
        for baja, alta in zip(ranking["FACTURACION_ANULADA"], ranking["FACTURACION_BRUTA"])
    ]

    if ranking_por == "Agente / mediador":
        ranking = add_mapeo_to_ranking_agente(ranking, mapeo_df)

    ranking = ranking.sort_values(metric, ascending=False).reset_index(drop=True)
    ranking.insert(0, "POSICION", range(1, len(ranking) + 1))

    return ranking, altas_detail, anulaciones_detail


def format_for_display(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if col in MONEY_COLUMNS:
            out[col] = out[col].apply(format_euro)
        elif col in PERCENT_COLUMNS:
            out[col] = out[col].apply(format_percent)
    return out


def to_excel_bytes(
    ranking: pd.DataFrame,
    altas: pd.DataFrame,
    anulaciones: pd.DataFrame,
    parametros: dict[str, object],
) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame([parametros]).to_excel(writer, index=False, sheet_name="PARAMETROS")
        ranking.to_excel(writer, index=False, sheet_name="RANKING")
        altas.to_excel(writer, index=False, sheet_name="DETALLE_ALTAS")
        anulaciones.to_excel(writer, index=False, sheet_name="DETALLE_ANULACIONES")
    return output.getvalue()


# ============================================================
# Imagen campaña Fórmula 1
# ============================================================


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            pass
    return ImageFont.load_default()


def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    box = draw.textbbox((0, 0), str(text), font=font)
    return box[2] - box[0]


def draw_text_fit(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: object, max_width: int, font_size: int, fill=(255, 255, 255), bold: bool = False) -> None:
    text = str(text)
    size = font_size
    font = get_font(size, bold=bold)
    while size > 10 and text_width(draw, text, font) > max_width:
        size -= 1
        font = get_font(size, bold=bold)
    draw.text(xy, text, font=font, fill=fill)


def image_cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    image = image.convert("RGB")
    return ImageOps.fit(image, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def format_int_es(value: object) -> str:
    try:
        return f"{int(round(float(value))):,}".replace(",", ".")
    except Exception:
        return "0"


def generate_formula1_campaign_image(
    ranking: pd.DataFrame,
    fecha_desde: date,
    fecha_hasta: date,
    ranking_por: str,
    metric_label: str,
    max_rows: int = 10,
) -> bytes:
    """Genera una imagen PNG con fondo Fórmula 1 y el ranking calculado."""
    if ranking.empty:
        raise ValueError("No hay datos para generar la imagen de campaña.")

    width, height = 1080, 1350
    bg = Image.open(BytesIO(base64.b64decode(FORMULA1_BACKGROUND_B64)))
    img = image_cover(bg, (width, height)).convert("RGBA")
    img = Image.alpha_composite(img, Image.new("RGBA", (width, height), (0, 0, 0, 115)))
    draw = ImageDraw.Draw(img)

    red = (225, 6, 0)
    dark = (16, 16, 20)
    white = (255, 255, 255)
    light = (238, 238, 238)
    gold = (255, 203, 92)

    # Cabecera
    draw.rounded_rectangle((50, 45, 1030, 238), radius=28, fill=(10, 10, 14, 215), outline=(255, 255, 255, 75), width=2)
    draw_text_fit(draw, (75, 78), "GRAN PREMIO DE DECESOS", 860, 62, fill=white, bold=True)
    draw.rectangle((75, 155, 560, 168), fill=red)
    subtitle = f"{ranking_por.upper()} · {metric_label.upper()} · {fecha_desde.strftime('%d/%m/%Y')} - {fecha_hasta.strftime('%d/%m/%Y')}"
    draw_text_fit(draw, (75, 193), subtitle, 850, 28, fill=light, bold=True)
    draw_text_fit(draw, (800, 78), "F1", 170, 68, fill=red, bold=True)

    top = ranking.copy().head(max_rows)
    table_x, table_y = 60, 305
    table_w = 960
    header_h = 72
    row_h = 72

    table_h = header_h + row_h * len(top) + 28
    draw.rounded_rectangle((table_x, table_y, table_x + table_w, table_y + table_h), radius=24, fill=(255, 255, 255, 226))
    draw.rounded_rectangle((table_x, table_y, table_x + table_w, table_y + header_h), radius=24, fill=red)
    draw.rectangle((table_x, table_y + 35, table_x + table_w, table_y + header_h), fill=red)

    headers = ["POS", "CÓDIGO", "AGENCIA", "PROVINCIA", "DECESOS"]
    col_x = [table_x + 32, table_x + 145, table_x + 300, table_x + 650, table_x + 825]
    col_w = [80, 130, 320, 150, 120]
    for x, header, w in zip(col_x, headers, col_w):
        draw_text_fit(draw, (x, table_y + 22), header, w, 30, fill=white, bold=True)

    for idx, (_, row) in enumerate(top.iterrows(), start=1):
        y = table_y + header_h + (idx - 1) * row_h
        fill = (248, 248, 248, 245) if idx % 2 else (230, 230, 230, 245)
        draw.rectangle((table_x, y, table_x + table_w, y + row_h), fill=fill)

        if idx <= 3:
            medal = gold if idx == 1 else ((194, 194, 199) if idx == 2 else (194, 128, 74))
            draw.ellipse((table_x + 26, y + 17, table_x + 70, y + 61), fill=medal)
            draw_text_fit(draw, (table_x + 40, y + 25), idx, 28, 24, fill=dark, bold=True)
        else:
            draw_text_fit(draw, (table_x + 41, y + 22), idx, 42, 30, fill=dark, bold=True)

        codigo = row.get("CODIGO", "")
        nombre = row.get("NOMBRE", "")
        provincia = row.get("PROVINCIA", "") if "PROVINCIA" in row.index else ""
        importe = row.get("FACTURACION_NETA", 0)

        draw_text_fit(draw, (col_x[1], y + 22), codigo, col_w[1], 30, fill=dark, bold=True)
        draw_text_fit(draw, (col_x[2], y + 22), nombre, col_w[2], 28, fill=dark, bold=False)
        draw_text_fit(draw, (col_x[3], y + 22), provincia, col_w[3], 28, fill=dark, bold=False)
        draw_text_fit(draw, (col_x[4], y + 22), format_int_es(importe), col_w[4], 30, fill=dark, bold=True)

    footer_y = table_y + table_h + 48
    draw.rounded_rectangle((60, footer_y, 1020, footer_y + 165), radius=24, fill=(10, 10, 14, 225))
    draw_text_fit(draw, (95, footer_y + 32), "RECTA FINAL DE CAMPAÑA", 590, 44, fill=white, bold=True)
    draw_text_fit(draw, (95, footer_y + 88), "Ranking generado automáticamente con facturación y anulaciones de Decesos", 830, 26, fill=light, bold=False)
    draw.rounded_rectangle((760, footer_y + 38, 980, footer_y + 118), radius=18, fill=red)
    draw_text_fit(draw, (795, footer_y + 57), "EUROPEA", 150, 34, fill=white, bold=True)
    draw_text_fit(draw, (812, footer_y + 94), "SEGUROS", 120, 19, fill=white, bold=True)

    out = BytesIO()
    img.convert("RGB").save(out, format="PNG", quality=95)
    return out.getvalue()


# ============================================================
# UI Streamlit
# ============================================================

st.set_page_config(page_title="Ranking personalizado Decesos", layout="wide")
st.title("Ranking personalizado Decesos")
st.caption(
    "Constructor flexible para generar rankings por agente o asesor usando facturación y anulaciones de Decesos. "
    "El rango se calcula con la fecha que selecciones y el tope de efecto se calcula siempre con POLIEFECT/POLIEFEC."
)

with st.sidebar:
    st.header("1. Archivos")
    facturacion_file = st.file_uploader("FACTURACION_DECESOS", type=["xls", "xlsx", "xlsm"])
    anulaciones_file = st.file_uploader("FACTURACION_ANULACIONES_DECESOS", type=["xls", "xlsx", "xlsm"])
    facturacion_asesor_file = st.file_uploader(
        "FACTURACION_DECESOS_ASESOR (solo si ranking por asesor)",
        type=["xls", "xlsx", "xlsm"],
    )
    mapeo_file = st.file_uploader(
        "MAPEO_MEDIADORES (opcional, para nombre/provincia)",
        type=["xls", "xlsx", "xlsm"],
    )

    st.header("2. Ranking")
    ranking_por = st.radio(
        "¿Qué ranking quieres?",
        ["Agente / mediador", "Asesor / comercial"],
        horizontal=False,
    )

if facturacion_file is None or anulaciones_file is None:
    st.info("Sube al menos FACTURACION_DECESOS y FACTURACION_ANULACIONES_DECESOS para empezar.")
    st.stop()

try:
    facturacion_df = read_excel_uploaded(facturacion_file)
    anulaciones_df = read_excel_uploaded(anulaciones_file)
    facturacion_asesor_df = read_excel_uploaded(facturacion_asesor_file) if facturacion_asesor_file else pd.DataFrame()
    mapeo_df = read_excel_uploaded(mapeo_file) if mapeo_file else pd.DataFrame()
except ImportError as error:
    st.error("Falta una librería para leer Excel antiguo .xls. Instala dependencias con: pip install xlrd openpyxl")
    st.exception(error)
    st.stop()
except Exception as error:
    st.error("No he podido leer alguno de los Excel.")
    st.exception(error)
    st.stop()

source_for_dates = (
    facturacion_asesor_df
    if ranking_por == "Asesor / comercial" and not facturacion_asesor_df.empty
    else facturacion_df
)

date_cols = available_date_columns(source_for_dates)

if not date_cols:
    st.error("No encuentro columnas de fecha en el archivo de facturación.")
    st.stop()

# Seleccion por defecto: GRABACION si existe; si no, FECHA_GRABACION; si no, POLIALTA.
default_date_index = 0
for preferred in ["GRABACION", "FECHA GRABACION", "FECHA_GRABACION", "POLIALTA"]:
    found = find_column(source_for_dates, (preferred,))
    if found in date_cols:
        default_date_index = date_cols.index(found)
        break

with st.form("ranking_form"):
    st.subheader("Parámetros del ranking")

    c1, c2, c3 = st.columns(3)

    with c1:
        date_column = st.selectbox(
            "¿Qué fecha quieres usar para el rango del ranking?",
            date_cols,
            index=default_date_index,
            help="Ejemplo: GRABACION para pólizas grabadas, POLIALTA para pólizas dadas de alta, etc.",
        )
        fecha_desde = st.date_input(
            "Fecha desde",
            value=date(date.today().year, 1, 1),
            format="DD/MM/YYYY",
        )

    with c2:
        fecha_hasta = st.date_input(
            "Fecha hasta",
            value=date.today(),
            format="DD/MM/YYYY",
        )
        usar_fecha_efecto_maxima = st.checkbox(
            "Fijar tope máximo de efecto",
            value=False,
            help="Este tope se aplica SIEMPRE sobre POLIEFECT/POLIEFEC, aunque el rango use GRABACION o POLIALTA.",
        )

    with c3:
        fecha_efecto_maxima_text = st.text_input(
            "Fecha efecto máxima (POLIEFECT)",
            value=f"31/12/{date.today().year}",
            help="Escribe la fecha en formato DD/MM/AAAA. Ejemplo: 31/05/2026 o 01/07/2026.",
        )
        excluded_products_text = st.text_input(
            "Productos excluidos",
            value=DEFAULT_EXCLUDED_PRODUCTS,
        )

    c4, c5, c6 = st.columns(3)

    with c4:
        metric_label = st.selectbox(
            "¿Qué parámetro quieres utilizar para ordenar el ranking?",
            [
                "Facturación neta",
                "Facturación bruta",
                "Pólizas grabadas",
                "Pólizas netas",
                "Facturación anulada",
                "Churn pólizas",
                "Churn facturación",
            ],
        )

    with c5:
        excluir_defuncion_siniestro = st.checkbox(
            "Excluir bajas por defunción / siniestro",
            value=True,
        )
        solo_bajas_altas_mismo_anio = st.checkbox(
            "En asesores: contar bajas solo si la póliza tuvo efecto ese mismo año",
            value=True,
        )
        generar_imagen_formula1 = st.checkbox(
            "Generar imagen campaña Fórmula 1",
            value=True,
        )

    with c6:
        asesor_codes_text = st.text_area(
            "Códigos excluidos en ranking asesor",
            value=DEFAULT_EXCLUDED_ASESOR_CODES,
            height=80,
        )
        asesor_prefixes_text = st.text_input(
            "Prefijos excluidos en ranking asesor",
            value=DEFAULT_EXCLUDED_ASESOR_PREFIXES,
        )

    submitted = st.form_submit_button("Crear ranking")

metric_map = {
    "Facturación neta": "FACTURACION_NETA",
    "Facturación bruta": "FACTURACION_BRUTA",
    "Pólizas grabadas": "POLIZAS_GRABADAS",
    "Pólizas netas": "POLIZAS_NETAS",
    "Facturación anulada": "FACTURACION_ANULADA",
    "Churn pólizas": "CHURN_POLIZAS",
    "Churn facturación": "CHURN_FACTURACION",
}

if submitted:
    try:
        if fecha_desde > fecha_hasta:
            raise ValueError("La fecha desde no puede ser posterior a la fecha hasta.")

        fecha_efecto_maxima_valor = None
        if usar_fecha_efecto_maxima:
            fecha_efecto_maxima_valor = parse_date_text(
                fecha_efecto_maxima_text,
                "Fecha efecto máxima",
            )

        ranking, altas_detail, anulaciones_detail = build_ranking(
            facturacion_df=facturacion_df,
            anulaciones_df=anulaciones_df,
            facturacion_asesor_df=facturacion_asesor_df,
            mapeo_df=mapeo_df,
            ranking_por=ranking_por,
            date_column=date_column,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            excluded_products=split_csv(excluded_products_text),
            fecha_efecto_maxima=fecha_efecto_maxima_valor,
            metric=metric_map[metric_label],
            excluir_defuncion_siniestro=excluir_defuncion_siniestro,
            solo_bajas_altas_mismo_anio=solo_bajas_altas_mismo_anio,
            excluded_asesor_codes=split_csv(asesor_codes_text),
            excluded_asesor_prefixes=split_csv(asesor_prefixes_text),
        )

        st.success(f"Ranking creado: {len(ranking)} filas")

        total_grabadas = int(ranking["POLIZAS_GRABADAS"].sum()) if not ranking.empty else 0
        total_anuladas = int(ranking["POLIZAS_ANULADAS"].sum()) if not ranking.empty else 0
        total_neta = float(ranking["FACTURACION_NETA"].sum()) if not ranking.empty else 0.0
        churn_total = total_anuladas / total_grabadas if total_grabadas else 0.0

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Facturación neta", format_euro(total_neta))
        k2.metric("Pólizas grabadas", total_grabadas)
        k3.metric("Pólizas anuladas", total_anuladas)
        k4.metric("Churn pólizas", format_percent(churn_total))

        st.subheader("Ranking")
        st.dataframe(format_for_display(ranking), use_container_width=True, hide_index=True)

        with st.expander("Ver detalle usado en el cálculo"):
            st.write("Altas filtradas")
            st.dataframe(altas_detail, use_container_width=True)
            st.write("Anulaciones filtradas")
            st.dataframe(anulaciones_detail, use_container_width=True)

        parametros = {
            "ranking_por": ranking_por,
            "mapeo_mediadores": "Aplicado" if not mapeo_df.empty else "No aplicado",
            "fecha_columna_rango": date_column,
            "fecha_desde": fecha_desde.strftime("%d/%m/%Y"),
            "fecha_hasta": fecha_hasta.strftime("%d/%m/%Y"),
            "tope_POLIEFECT_aplicado": (
                fecha_efecto_maxima_valor.strftime("%d/%m/%Y")
                if fecha_efecto_maxima_valor
                else "No aplicado"
            ),
            "productos_excluidos": excluded_products_text,
            "ordenado_por": metric_label,
            "excluir_defuncion_siniestro": excluir_defuncion_siniestro,
            "solo_bajas_altas_mismo_anio_asesores": solo_bajas_altas_mismo_anio,
        }

        excel_bytes = to_excel_bytes(
            ranking,
            altas_detail,
            anulaciones_detail,
            parametros,
        )

        st.download_button(
            "Descargar ranking en Excel",
            data=excel_bytes,
            file_name="ranking_personalizado_decesos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


        if generar_imagen_formula1:
            st.subheader("Imagen campaña Fórmula 1")
            imagen_formula1 = generate_formula1_campaign_image(
                ranking=ranking,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                ranking_por=ranking_por,
                metric_label=metric_label,
                max_rows=10,
            )
            st.image(imagen_formula1, caption="Previsualización imagen campaña Fórmula 1", use_container_width=True)
            st.download_button(
                "Descargar imagen campaña Fórmula 1",
                data=imagen_formula1,
                file_name="ranking_formula1_decesos.png",
                mime="image/png",
            )

    except Exception as error:
        st.error("No he podido crear el ranking con estos parámetros.")
        st.exception(error)
