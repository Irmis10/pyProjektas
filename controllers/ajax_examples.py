from random import randint
def index():
    return dict()

def data():
    if not session.m or len(session.m)==10: session.m=[]
    if request.vars.q: session.m.append(request.vars.q)
    session.m.sort()
    return TABLE(*[TR(v) for v in session.m]).xml()

def start():
    session.tikslas = randint(1, 10)
    session.spejimai = []
    return A("eik spėliot..", _href="index")

def speliones():
    if session.spejimai is None:
        redirect('start')


    rez2 = "bandyk laimę.."
    if request.vars.kiek:  # None, ""  veikia kaip Fasle
        kiek = int(request.vars.kiek)
        session.spejimai.append(kiek)  # papildom spejimus
        if kiek == session.tikslas:
            rez2 = "Valio!"

    return DIV( BEAUTIFY(request.vars),
               rez2, UL(session.spejimai),
              )
