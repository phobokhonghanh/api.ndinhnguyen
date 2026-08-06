import json

RAW_BANKS_JSON = """[
  {
    "code": "ABB",
    "name": "Ngân hàng TMCP An Bình",
    "short_name": "ABBANK",
    "bin": "970425",
    "logo": "https://api.vietqr.io/img/ABB.png"
  },
  {
    "code": "ACB",
    "name": "Ngân hàng TMCP Á Châu",
    "short_name": "ACB",
    "bin": "970416",
    "logo": "https://api.vietqr.io/img/ACB.png"
  },
  {
    "code": "VBA",
    "name": "Ngân hàng Nông nghiệp và Phát triển Nông thôn Việt Nam",
    "short_name": "Agribank",
    "bin": "970405",
    "logo": "https://api.vietqr.io/img/AGRIBANK.png"
  },
  {
    "code": "BAB",
    "name": "Ngân hàng TMCP Bắc Á",
    "short_name": "Bac A Bank",
    "bin": "970409",
    "logo": "https://api.vietqr.io/img/BAB.png"
  },
  {
    "code": "BVB",
    "name": "Ngân hàng TMCP Bảo Việt",
    "short_name": "BaoViet Bank",
    "bin": "970438",
    "logo": "https://api.vietqr.io/img/BVB.png"
  },
  {
    "code": "BIDV",
    "name": "Ngân hàng TMCP Đầu tư và Phát triển Việt Nam",
    "short_name": "BIDV",
    "bin": "970418",
    "logo": "https://api.vietqr.io/img/BIDV.png"
  },
  {
    "code": "EIB",
    "name": "Ngân hàng TMCP Xuất Nhập Khẩu Việt Nam",
    "short_name": "Eximbank",
    "bin": "970431",
    "logo": "https://api.vietqr.io/img/EIB.png"
  },
  {
    "code": "GPB",
    "name": "Ngân hàng Thương mại TNHH MTV Dầu Khí Toàn Cầu",
    "short_name": "GPBank",
    "bin": "970408",
    "logo": "https://api.vietqr.io/img/GPB.png"
  },
  {
    "code": "HDB",
    "name": "Ngân hàng TMCP Phát triển Thành phố Hồ Chí Minh",
    "short_name": "HDBank",
    "bin": "970437",
    "logo": "https://api.vietqr.io/img/HDB.png"
  },
  {
    "code": "ICB",
    "name": "Ngân hàng TMCP Công Thương Việt Nam",
    "short_name": "VietinBank",
    "bin": "970415",
    "logo": "https://api.vietqr.io/img/ICB.png"
  },
  {
    "code": "KLB",
    "name": "Ngân hàng TMCP Kiên Long",
    "short_name": "Kienlongbank",
    "bin": "970452",
    "logo": "https://api.vietqr.io/img/KLB.png"
  },
  {
    "code": "LPB",
    "name": "Ngân hàng TMCP Lộc Phát Việt Nam",
    "short_name": "LPBank",
    "bin": "970449",
    "logo": "https://api.vietqr.io/img/LPB.png"
  },
  {
    "code": "MB",
    "name": "Ngân hàng TMCP Quân Đội",
    "short_name": "MBBank",
    "bin": "970422",
    "logo": "https://api.vietqr.io/img/MB.png"
  },
  {
    "code": "MSB",
    "name": "Ngân hàng TMCP Hàng Hải Việt Nam",
    "short_name": "MSB",
    "bin": "970426",
    "logo": "https://api.vietqr.io/img/MSB.png"
  },
  {
    "code": "NAB",
    "name": "Ngân hàng TMCP Nam Á",
    "short_name": "Nam A Bank",
    "bin": "970428",
    "logo": "https://api.vietqr.io/img/NAB.png"
  },
  {
    "code": "NCB",
    "name": "Ngân hàng TMCP Quốc Dân",
    "short_name": "NCB",
    "bin": "970419",
    "logo": "https://api.vietqr.io/img/NCB.png"
  },
  {
    "code": "OCB",
    "name": "Ngân hàng TMCP Phương Đông",
    "short_name": "OCB",
    "bin": "970448",
    "logo": "https://api.vietqr.io/img/OCB.png"
  },
  {
    "code": "Oceanbank",
    "name": "Ngân hàng Thương mại TNHH MTV Đại Dương",
    "short_name": "OceanBank",
    "bin": "970414",
    "logo": "https://api.vietqr.io/img/OCEANBANK.png"
  },
  {
    "code": "PGB",
    "name": "Ngân hàng TMCP Thịnh vượng và Phát triển",
    "short_name": "PGBank",
    "bin": "970430",
    "logo": "https://api.vietqr.io/img/PGB.png"
  },
  {
    "code": "PVCB",
    "name": "Ngân hàng TMCP Đại Chúng Việt Nam",
    "short_name": "PVcomBank",
    "bin": "970412",
    "logo": "https://api.vietqr.io/img/PVCB.png"
  },
  {
    "code": "STB",
    "name": "Ngân hàng TMCP Sài Gòn Thương Tín",
    "short_name": "Sacombank",
    "bin": "970403",
    "logo": "https://api.vietqr.io/img/STB.png"
  },
  {
    "code": "SGB",
    "name": "Ngân hàng TMCP Sài Gòn Công Thương",
    "short_name": "SaigonBank",
    "bin": "970400",
    "logo": "https://api.vietqr.io/img/SGB.png"
  },
  {
    "code": "SCB",
    "name": "Ngân hàng TMCP Sài Gòn",
    "short_name": "SCB",
    "bin": "970429",
    "logo": "https://api.vietqr.io/img/SCB.png"
  },
  {
    "code": "SEAB",
    "name": "Ngân hàng TMCP Đông Nam Á",
    "short_name": "SeABank",
    "bin": "970440",
    "logo": "https://api.vietqr.io/img/SEAB.png"
  },
  {
    "code": "SHB",
    "name": "Ngân hàng TMCP Sài Gòn - Hà Nội",
    "short_name": "SHB",
    "bin": "970443",
    "logo": "https://api.vietqr.io/img/SHB.png"
  },
  {
    "code": "TCB",
    "name": "Ngân hàng TMCP Kỹ thương Việt Nam",
    "short_name": "Techcombank",
    "bin": "970407",
    "logo": "https://api.vietqr.io/img/TCB.png"
  },
  {
    "code": "TPB",
    "name": "Ngân hàng TMCP Tiên Phong",
    "short_name": "TPBank",
    "bin": "970423",
    "logo": "https://api.vietqr.io/img/TPB.png"
  },
  {
    "code": "VAB",
    "name": "Ngân hàng TMCP Việt Á",
    "short_name": "VietABank",
    "bin": "970427",
    "logo": "https://api.vietqr.io/img/VAB.png"
  },
  {
    "code": "VCB",
    "name": "Ngân hàng TMCP Ngoại Thương Việt Nam",
    "short_name": "Vietcombank",
    "bin": "970436",
    "logo": "https://api.vietqr.io/img/VCB.png"
  },
  {
    "code": "VBB",
    "name": "Ngân hàng TMCP Việt Nam Thương Tín",
    "short_name": "VietBank",
    "bin": "970433",
    "logo": "https://api.vietqr.io/img/VBB.png"
  },
  {
    "code": "VPB",
    "name": "Ngân hàng TMCP Việt Nam Thịnh Vượng",
    "short_name": "VPBank",
    "bin": "970432",
    "logo": "https://api.vietqr.io/img/VPB.png"
  },
  {
    "code": "VRB",
    "name": "Ngân hàng Liên doanh Việt - Nga",
    "short_name": "VRB",
    "bin": "970421",
    "logo": "https://api.vietqr.io/img/VRB.png"
  }
]
"""

def load_banks_json() -> list[dict]:
    return json.loads(RAW_BANKS_JSON)

