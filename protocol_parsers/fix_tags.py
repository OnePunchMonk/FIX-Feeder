FIX_TAGS = {
    8: "BeginString",
    9: "BodyLength",
    35: "MsgType",
    49: "SenderCompID",
    56: "TargetCompID",
    34: "MsgSeqNum",
    52: "SendingTime",
    11: "ClOrdID",
    41: "OrigClOrdID",
    55: "Symbol",
    54: "Side",
    38: "OrderQty",
    40: "OrdType",
    44: "Price",
    10: "Checksum"
}

MSG_TYPE_MAP = {
    "D": "NewOrderSingle",
    "F": "OrderCancelRequest",
    "H": "OrderStatusRequest"
}

SIDE_MAP = {
    "1": "Buy",
    "2": "Sell"
}