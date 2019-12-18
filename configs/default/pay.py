import os


# 是否启用支付宝系统
USE_ALIPAY = bool(os.getenv("USE_ALIPAY"))

# 支付宝APP_ID
ALIPAY_APP_ID = os.getenv("ALIPAY_APP_ID", "")

# 支付宝app私钥
ALIPAY_APP_PRIVATE_KEY_STRING = os.getenv("ALIPAY_APP_PRIVATE_KEY_STRING")

# 支付宝公钥
ALIPAY_PUBLIC_KEY_STRING = os.getenv("ALIPAY_PUBLIC_KEY_STRING")

# 支付订单提示信息 修改请保留 {} 用于动态生成金额
ALIPAY_TRADE_INFO = "谜之屋的{}元充值码"
