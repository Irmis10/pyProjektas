# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This is a sample controller
# this file is released under public domain and you can use without limitations
# -------------------------------------------------------------------------
import random

# ---- example index page ----
def index():
    redirect( URL('posts') )

# ---- Action for login/register/etc (required for auth) -----
def user():
    """
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    also notice there is http://..../[app]/appadmin/manage/auth to allow administrator to manage users
    """
    return dict(form=auth())

# ---- action to server uploaded static content (required) ---
@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)

def fill_cat():
    for x in db(db.posts).select():
        x.update_record(category=random.randint(1, 3))
    redirect(URL('posts'))

def populate():
    if not request.is_local:  #apsauga, kad viešai pahost'inus negalėtų nieks generuot fake duomenų
        return "localhost only"
    from gluon.contrib.populate import populate
    # /skelbimai/default/populate/<table>
    # pvz:
    # /skelbimai/default/populate/auth_user
    # /skelbimai/default/populate/posts
    table = request.args[0]

    if request.vars.extra == 'clear':
        # /skelbimai/default/populate/posts?extra=clear
        db( db[table] ) .delete()

    populate(db[table], 10)   # db yra tarsi lentelių žodynas
    # populate(db.posts ,10)  # db['posts']
    return db( db[table] ).select()

def populate_fresh_db():

    db.categories.insert( title='katės')
    db.categories.insert( title='kompai')
    db.categories.insert( title='dovanoja')

    from gluon.contrib.populate import populate
    populate(db.auth_user, 3)
    populate(db.posts, 10)

    return dict(
        categories=db(db.categories).select(),
        authors=db(db.auth_user).select(),
        posts=db(db.posts).select(),
    )



def beautify_posts( rows ):
    result =  UL(
               [ LI(
                   DIV("[%s] " % x.category,  x.author,
                       I( x.action_ ), " ",
                       x.miestas_name, ": ",
                       B(x.title[0:40]),   # ribojam rodomo title ilgį iki 40
                       BR(), x.body[:100]
                       ),
                   A( "Rodyti visą info" , _class='btn btn-info', _href=URL('post', args=x.id))
               )
                for x in rows]
            )
    return result

def posts():
    """ Skelbimų esminiai reikalai.
    priklausomai, kaip suformuluotas url'as, rodys skirtingus reikalus

    /skelbimai/default/posts -- post'ų sąrašas
    """

    # http://tiny.lt/pycrud 
    rows = db().select( db.posts.ALL )   #  db.posts.ALL atitinka SELECT *

    # UŽDUOTIS: padaryti gražų sąrašą su link'ais į post'o peržiūrą
    rows = beautify_posts( rows )
    
    new =  A( "..new..",  _class='btn btn-warning', _href=URL('post', args=["", "edit"]) )

    return dict( rows=rows,   # {'rows':rows}
            new=new # naujo įrašo kūrimo link'as
            ) 


def post():
    """ Vieno skelbimo reikalai
    /skelbimai/default/post/<id> -- konkretus post'as
    /skelbimai/default/post/<id>/edit -- konkretaus post'o redagavimas
    /skelbimai/default/post//edit  -- kuriam naują post'ą
    """
    try:  
        id = int(request.args[0])
        record = db.posts[id]
    except:    
        record = None
        id=""

    edit = request.args(1) # lenkti skliaustai, jei neranda index'o grąžina None
    can_edit = False
    edit_link = ""
    # jeigu yra prisijungęs user'is 
    if auth.is_logged_in():

        if record: # jeigu jau yra skelbimas
            # patikrina ar skelbimo autorius yra  dabartinis user'is
            if auth.user.id == record.author:

                edit_link = A("edit",_class='btn btn-success',_href=URL(args=[id, 'edit']))

                can_edit = edit=='edit'
        
        else: # jeigu naujas skelbimas
            can_edit = edit=='edit'

    if record==None and not can_edit:  # kai nėra prasmės kažką rodyt
        redirect(URL("posts"))

    form = SQLFORM(db.posts, record, 
                     readonly= not can_edit, # True arba False
                     showid=False
            )
    
    if form.process().accepted:  # form.process() reikia, kad įrašytų į DB
        redirect(URL("posts"))
    
    return dict( 
        form=form, 
        edit_link = edit_link
    )

    
def search():
    cat_title = request.args(0)

    # leidžiam laukelius palikti tuščius
    miestas = db.posts.miestas_name  # patogesnį kintamąjį
    miestas.requires = IS_EMPTY_OR( miestas.requires )
    db.posts.action_ .requires = IS_EMPTY_OR ( db.posts.action_ .requires   )

    # Paieškos forma
    search_form = SQLFORM.factory(
        db.posts.category,
        db.posts.miestas_name , # arba:  miestas
        db.posts.action_,
        Field("words", label="žodžiai")
    )

    # "Suvirškinam formą"
    if search_form.process(keepvalues=True).accepted:
        cat_id = search_form.vars.category
        if cat_id:  # jeigu kategorija nurodyta
            cat_title = db.categories[cat_id].title

    # sukonstruojam FILTRĄ  pagal formoje pateiktus laukus
    filter = True  # parenka viską (ir leidžia papildyt su & )
    if cat_title:
        # &=  filtrą PAPILDO nauja sąlyga
        filter  &=   db.categories.title == cat_title

    if search_form.vars.miestas_name:
        filter  &=   db.posts.miestas_name == search_form.vars.miestas_name

    if search_form.vars.action_:
        filter  &=   db.posts.action_ == search_form.vars.action_

    words = search_form.vars.words
    if words:
        words = words.split()
        filter &= (
                  db.posts.title.contains( words, all=True )
                   |
                   db.posts.body.contains( words, all=True )
                  )

    rows = ( db( filter ).  # WHERE
        select (                     
            db.posts.ALL,  # SELECT posts.*
            join= db.categories.on( db.categories.id == db.posts.category) # JOIN
        )
    )
    
    return dict(
        rows=beautify_posts (rows),
        form=search_form
        #, cat_title=cat_title
    )


# mandras būdas peržiūrėt lentelės įrašus
@auth.requires_login()
def grid():
    return dict( content = SQLFORM.grid( db.posts.author==auth.user.id ) )

@auth.requires_login()
def admin():
    # http://tiny.lt/pycrud
    rows = db(db.posts.author==auth.user.id).select(db.posts.ALL)  # db.posts.ALL atitinka SELECT *

    # UŽDUOTIS: padaryti gražų sąrašą su link'ais į post'o peržiūrą
    rows = beautify_posts(rows)

    new = A("..new..", _class='btn btn-warning', _href=URL('post', args=["", "edit"]))

    return dict(rows=rows,  # {'rows':rows}
                new=new  # naujo įrašo kūrimo link'as
                )

def post_del ():
    try:
        id = int(request.args[0])
    except:
        return "kazkur i kosmosa..."
    db(db.lenta.kas == "b").delete
    redirect(URL('admin'))



