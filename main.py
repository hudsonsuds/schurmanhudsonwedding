from flask import Flask
app = Flask(__name__)
app.config['DEBUG'] = True

from flask import request, render_template, flash, url_for, redirect
import os, logging
from google.appengine.ext import ndb

# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.

"""
Define models for RSVP
"""

class Invite(ndb.Model):
    guests = ndb.KeyProperty(kind="Guest", repeated=True)
    rehearsal_invite = ndb.BooleanProperty()
    wedding_invite = ndb.BooleanProperty()
    advice = ndb.TextProperty()
    responded = ndb.BooleanProperty(default=False)
    
    
class Guest(ndb.Model):
    name = ndb.StringProperty()
    email = ndb.StringProperty(repeated=True)
    phone = ndb.StringProperty(repeated=True)
    rehearsal_rsvp = ndb.StringProperty()
    wedding_rsvp = ndb.StringProperty()

"""
Define helper functions
"""

def lookupInvite(qstring):
    logging.info("Query lookup : %s" % qstring)
    
    ## Check for matches
    email_match = Guest.query(Guest.email == str(qstring)).get()
    phone_match = Guest.query(Guest.phone == str(qstring)).get()

    if email_match:
        logging.info("Email")
        logging.info(email_match.name)
        
        invite = Invite.query(Invite.guests == email_match.key).get()
        return invite
        
    elif phone_match:
        logging.info("Phone")
        logging.info(phone_match.name)
        
        invite = Invite.query(Invite.guests == phone_match.key).get()
        return invite
        
    else:
        return False
    
    

"""
Define routing rules
"""

@app.route('/')
def index():
    return render_template('home.html')
    
@app.route('/our_story')
def our_story():
    return redirect(url_for("index"))
    ##return render_template('our_story.html')

@app.route('/wedding')
def wedding():
    return render_template('wedding.html')

@app.route('/weekend')
def timeline():
    return render_template('timeline.html')

@app.route('/travel')
def travel():
    return render_template('travel.html')

@app.route('/rsvp', methods=['GET', 'POST'])
def rsvp():
    if request.method == 'GET':
        logging.info('Get request')
        
        ## Change return template to rsvp.html for active form
        return render_template('rsvp_hold.html', not_found=False)
        
    if request.method == 'POST':
        logging.info('Post request')
        registration_id = request.form.get("registration_id")
        
        ## Lookup invitation
        invite = lookupInvite(registration_id)
        
        if not invite:
            return render_template('rsvp.html', not_found=registration_id)
        else:   
            ## Make list of guests to return
            guests = []
        
            for guest in invite.guests:
                guests.append(Guest.query(Guest.key == guest).get())
            
            if invite.responded:

                ## Confirmation page
                return render_template('confirm.html', invite = invite, guests = guests)
                
            else:
                ## Registration page
                return render_template('register.html', invite = invite, guests = guests)


                
@app.route('/rsvp_submit', methods=['POST'])
def rsvp_submit():
    logging.info('RSVP submit')
    
    ## Get invite key and lookup invite & guests
    invite_key = ndb.Key(urlsafe=request.form.get("invite_key"))
    invite = invite_key.get()
    
    guests = []
    for guest in invite.guests:
        guests.append(Guest.query(Guest.key == guest).get())
    
    
    ## Check for rehearsal invite
    if invite.rehearsal_invite:
        
        logging.info("Rehearsal Invite:")
        
        ## Iterate through guests with responses
        for guest in invite.guests:
            
            thisGuest = guest.get()
            
            ## Get rsvp
            r_rsvp = request.form.get("r-%s" % guest.urlsafe())
            logging.info(thisGuest.name + " " + r_rsvp)
            
            ## Add to datastore
            thisGuest.rehearsal_rsvp = r_rsvp
            thisGuest.put()

    ## Check for wedding invite
    if invite.wedding_invite:
        
        logging.info("Wedding Invite:")
        
        ## Iterate through guests with responses
        for guest in invite.guests:
            
            thisGuest = guest.get()
            
            ## Get rsvp
            w_rsvp = request.form.get("w-%s" % guest.urlsafe())
            logging.info(thisGuest.name + " " + w_rsvp)
            
            ## Add to datastore
            thisGuest.wedding_rsvp = w_rsvp
            thisGuest.put()
            
        ## Add advice for the bride and groom
        invite.advice = request.form.get("advice")
        invite.responded = True
        invite.put()
    
    return render_template('confirm.html', invite = invite, guests = guests)

@app.route('/load')
def load_data():
    ## TODO: Figure out how to load data into datastore. Right now, thinking:
    ## TODO: 1) Create a spreadsheet with the data in guest:invite format
    ## TODO: 2) Write a small function that parses over CSV and loads in
    ## TODO: 3) Think about how we get this out too -- after RSVPs? Trix?
    ## TODO:    Or could just have a page that dumps out all invites & replies.
    g1 = Guest(name = "Julia Schurman", email = ["julia.aschurman@gmail.com","juliaaschurman@gmail.com"],phone=["4017427003"])
    g2 = Guest(name = "Matt Hudson", email = ["matt.b.hudson@gmail.com", 'Huddy@umich.edu'], phone = ["6506483766", "8473621773"])
    
    ##g1.put()
    ##g2.put()
    
    g1_key = Guest.query(Guest.name == "Julia Schurman").get().key
    g2_key = Guest.query(Guest.name == "Matt Hudson").get().key
    
    i1 = Invite(guests = [g1_key, g2_key], rehearsal_invite=True, wedding_invite=True)
    i1.put()
    
    return redirect(url_for('index'))

@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, nothing at this URL.', 404