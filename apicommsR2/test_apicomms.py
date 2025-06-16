#!/home/pablo/Spymovil/python/proyectos/APICOMMS/venv/bin/python

import requests
import itertools

URL_BASE = "http://localhost:5000/apidlg?"


def test_fwdlgx():
    TYPE = "FWDLGX"
    ID = "SPQTEST"
    HW = ["SPQ_AVRDA_R1", "SPQ_AVRDA_R2"]
    VER = ["1.0.0", "1.0.1","1.0.2", "1.0.3"]

    d_frames = {
        "BASE": { "SEND": "&CLASS=CONF_BASE&UID=ABDCZXYT&IMEI=12345&ICCID=999888&HASH=0x12",
            "RSP": "CLASS=CONF_BASE&TPOLL=60&TDIAL=900&PWRMODO=CONTINUO&PWRON=1530&PWROFF=1550"
        },
        "AINPUTS": { "SEND": "&CLASS=CONF_AINPUTS&HASH=0x15",
            "RSP": "CLASS=CONF_AINPUTS&A0=TRUE,PRESA,0,20,0.0,6.0,0.0&A1=TRUE,PRESB,0,20,0.0,6.0,0.0&A2=TRUE,PRESC,0,20,0.0,6.0,0.0"
        },
        "COUNTERS": { "SEND": "&CLASS=CONF_COUNTERS&HASH=0x12",
            "RSP": "CLASS=CONF_COUNTERS&C0=TRUE,CAU0,5.3,CAUDAL"
        },
        "MODBUS": {"SEND": "&CLASS=CONF_MODBUS&HASH=0x12",
            "RSP": "CLASS=CONF_MODBUS&ENABLE=TRUE&LOCALADDR=1&M0=TRUE,Q0,2,0,2,3,FLOAT,C1032,0&M1=FALSE,Q1,3,0,2,3,FLOAT,C1032,0&M2=FALSE,X,2,0,2,0,FLOAT,C1032,0&M3=FALSE,X,2,0,2,0,FLOAT,C1032,0&M4=FALSE,X,2,0,2,0,FLOAT,C1032,0"
        },
        "CONSIGNA": { "SEND": "&CLASS=CONF_CONSIGNA&HASH=0x12",
            "RSP": "CLASS=CONF_CONSIGNA&ENABLE=TRUE&DIURNA=730&NOCTURNA=2300"
        }, 
        "DATA": { "SEND": "&CLASS=DATA&DATE=230321&TIME=094504&A0=0.00&A1=0.00&A2=0.00&C0=0.000&C1=0.000&bt3v3=3.87&bt12v=12.76",
            "RSP": "CLASS=DATA&CLOCK="
        }
    }

    # Combino las versiones con los hardwares
    it = itertools.product( HW, VER)
    for (hw,ver) in it:
        frame_base = f"ID={ID}&TYPE={TYPE}&VER={ver}&HW={hw}"
        
        for ftype in d_frames:
            f_payload = d_frames[ ftype ] ['SEND']
            f_response = d_frames[ ftype] ['RSP']
            frame = URL_BASE + frame_base + f_payload
            #print(frame)
            rsp = requests.get(frame)
            if rsp.status_code == 200:
                if f_response in rsp.text:
                    print(f"{ftype} ver={ver}, hw={hw} OK")
                else:
                    print("ERROR")
            else:
                print("RSP ERROR")

def test_spqavrda():
    TYPE = "SPQ_AVRDA"
    ID = "SPQTEST"
    HW = ["SPQ_AVRDA_R1", "SPQ_AVRDA_R2"]
    VER = ["1.0.0", "1.1.0","1.2.0", "1.3.0"]

    d_frames = {
        "BASE": { "SEND": "&CLASS=CONF_BASE&UID=ABDCZXYT&IMEI=12345&ICCID=999888&HASH=0x12",
            "RSP": "CLASS=CONF_BASE&TPOLL=60&TDIAL=900&PWRMODO=CONTINUO&PWRON=1530&PWROFF=1550"
        },
        "AINPUTS": { "SEND": "&CLASS=CONF_AINPUTS&HASH=0x15",
            "RSP": "CLASS=CONF_AINPUTS&A0=TRUE,PRESA,0,20,0.0,6.0,0.0&A1=TRUE,PRESB,0,20,0.0,6.0,0.0&A2=TRUE,PRESC,0,20,0.0,6.0,0.0"
        },
        "COUNTERS": { "SEND": "&CLASS=CONF_COUNTERS&HASH=0x12",
            "RSP": "CLASS=CONF_COUNTERS&C0=TRUE,CAU0,5.3,CAUDAL"
        },
        "MODBUS": {"SEND": "&CLASS=CONF_MODBUS&HASH=0x12",
            "RSP": "CLASS=CONF_MODBUS&ENABLE=TRUE&LOCALADDR=1&M0=TRUE,Q0,2,0,2,3,FLOAT,C1032,0&M1=FALSE,Q1,3,0,2,3,FLOAT,C1032,0&M2=FALSE,X,2,0,2,0,FLOAT,C1032,0&M3=FALSE,X,2,0,2,0,FLOAT,C1032,0&M4=FALSE,X,2,0,2,0,FLOAT,C1032,0"
        },
        "CONSIGNA": { "SEND": "&CLASS=CONF_CONSIGNA&HASH=0x12",
            "RSP": "CLASS=CONF_CONSIGNA&ENABLE=TRUE&DIURNA=730&NOCTURNA=2300"
        }, 
        "DATA": { "SEND": "&CLASS=DATA&DATE=230321&TIME=094504&A0=0.00&A1=0.00&A2=0.00&C0=0.000&C1=0.000&bt3v3=3.87&bt12v=12.76",
            "RSP": "CLASS=DATA&CLOCK="
        }
    }

    # Combino las versiones con los hardwares
    it = itertools.product( HW, VER)
    for (hw,ver) in it:
        frame_base = f"ID={ID}&TYPE={TYPE}&VER={ver}&HW={hw}"
        
        for ftype in d_frames:
            f_payload = d_frames[ ftype ] ['SEND']
            f_response = d_frames[ ftype] ['RSP']
            frame = URL_BASE + frame_base + f_payload
            #print(frame)
            rsp = requests.get(frame)
            if rsp.status_code == 200:
                if f_response in rsp.text:
                    print(f"{ftype} ver={ver}, hw={hw} OK")
                else:
                    print("ERROR")
            else:
                print("RSP ERROR")


if __name__ == '__main__':
    #test_fwdlgx()
    test_spqavrda()



