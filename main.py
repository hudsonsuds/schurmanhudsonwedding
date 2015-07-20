from flask import Flask
app = Flask(__name__)
app.config['DEBUG'] = True

from flask import request, render_template, flash, url_for, redirect
import os, logging
from google.appengine.ext import ndb
from google.appengine.api import mail


# Define application models
class Invite(ndb.Model):
    name = ndb.StringProperty()
    guests = ndb.KeyProperty(kind="Guest", repeated=True)
    rehearsal_invite = ndb.BooleanProperty()
    brunch_invite = ndb.BooleanProperty()
    hotel = ndb.StringProperty()
    arrival_date = ndb.StringProperty()
    departure_date = ndb.StringProperty()
    advice = ndb.StringProperty()
    responded = ndb.BooleanProperty(default=False)
    
class Guest(ndb.Model):
    name = ndb.StringProperty()
    drinks_rsvp = ndb.StringProperty(default="No Response")
    rehearsal_rsvp = ndb.StringProperty(default="No Response")
    wedding_rsvp = ndb.StringProperty(default="No Response")
    brunch_rsvp = ndb.StringProperty(default="No Response")
        
# App Routing rules
@app.route('/')
def index():
    return render_template('home.html')
    
@app.route('/wedding')
def wedding():
    
    img_urls = ['1-1', '1-2', '1-3']
    
    return render_template('wedding.html', img_urls = img_urls)

@app.route('/weekend')
def weekend():
    
    img_urls = ['4-1', '4-2', '4-3']
    
    return render_template('weekend.html', img_urls = img_urls)

@app.route('/travel')
def travel():
    
    img_urls = ['2-1', '2-2', '2-3']
    
    return render_template('travel.html', img_urls = img_urls)
    
@app.route('/rsvp_exact', methods=['POST'])
def rsvp_exact():
    
    # Get invite key and lookup invite & guests
    invite_key = ndb.Key(urlsafe=request.form.get("invite"))
    invite = invite_key.get()

    # Make list of guests to return
    guests = []
        
    for guest in invite.guests:
        guests.append(Guest.query(Guest.key == guest).get())
            
    if invite.responded:

        # Confirmation page
        return render_template('confirm.html', invite = invite, guests = guests)
                
    else:
        # Registration page
        return render_template('register.html', invite = invite, guests = guests, guest_count = len(guests))

@app.route('/rsvp', methods=['GET', 'POST'])
def rsvp():
    
    if request.method == 'GET':        
        
        # Change return template to rsvp.html for active form
        return render_template('rsvp.html', not_found=False, multiple = False)
        
    if request.method == 'POST':
        registration_id = request.form.get("registration_id")
        
        # Lookup invitation
        invite = Invite.query(Invite.name == registration_id).fetch()
        
        # If no invitation        
        if not invite:
            logging.info("No invitation found for %s" % registration_id)
            
            return render_template('rsvp.html', not_found=registration_id, multiple = False)
        
        # More than one invitation    
        elif len(invite) > 1:
            logging.info("Multiple invitations found for %s" % registration_id)
            
            return render_template('rsvp.html', multiple = True, invites = invite)
            
        # Exact match on one invitation
        else:   
            # Make list of guests to return
            guests = []
        
            for guest in invite[0].guests:
                guests.append(Guest.query(Guest.key == guest).get())
            
            if invite[0].responded:

                # Confirmation page
                return render_template('confirm.html', invite = invite[0], guests = guests)
                
            else:
                # Registration page
                return render_template('register.html', invite = invite[0], guests = guests, guest_count = len(guests))
                
@app.route('/rsvp_submit', methods=['POST'])
def rsvp_submit():
    logging.info('RSVP submit')
    
    # Get invite key and lookup invite & guests
    invite_key = ndb.Key(urlsafe=request.form.get("invite_key"))
    invite = invite_key.get()
    
    guests = []
        
    # Iterate through guests with responses
    for guest in invite.guests:
            
        thisGuest = guest.get()        
            
        # Get wedding rsvp
        thisGuest.wedding_rsvp = request.form.get("w-%s" % guest.urlsafe())
        thisGuest.drinks_rsvp = request.form.get("d-%s" % guest.urlsafe())
        thisGuest.brunch_rsvp = request.form.get("b-%s" % guest.urlsafe())
        
        # Add rehearsal invite if they're invited
        if invite.rehearsal_invite:
            thisGuest.rehearsal_rsvp = request.form.get("r-%s" % guest.urlsafe())
            
        # Add to guest list
        guests.append(thisGuest)
    
    # Update guests in datastore        
    ndb.put_multi(guests)
    
    # Add advice for the bride and groom
    invite.advice = request.form.get("advice")
    invite.hotel = request.form.get("hotel")
    invite.arrival_date = request.form.get("arrival_date")
    invite.departure_date = request.form.get("departure_date")
    invite.responded = True
    invite.put()
    
    # Send mail to Julia than an RSVP happeend
    message = mail.EmailMessage(sender="Matt Hudson <matt.b.hudson@gmail.com>",
                                subject="The %s family RSVP'd" % invite.name)

    message.to = "Julia Schurman <julia.aschurman@gmail.com>"
    message.body = """
    Hi Julia!

    Good news! The %s family just RSVP'd.
    
    juliamattwedding.com/teamone
    
    Love you,
    
    Matt
    
    """ % invite.name

    message.send()
    
    return render_template('confirm.html', invite = invite, guests = guests)
    
@app.route('/teamone')
def teamone():
    
    # Get list of invites in datastore
    invites = Invite.query().fetch()
    
    # Empty variables
    rsvps = [{"key": "Yes", "color": "#4f99b4", "values": [{"label":"Drinks", "value":0},\
                                                           {"label":"Rehearsal", "value":0},\
                                                           {"label":"Wedding", "value":0},\
                                                           {"label":"Brunch", "value":0}]},\
             {"key": "No", "color": "#d67777", "values": [{"label":"Drinks", "value":0},\
                                                           {"label":"Rehearsal", "value":0},\
                                                           {"label":"Wedding", "value":0},\
                                                           {"label":"Brunch", "value":0}]},\
             {"key": "No Response", "color": "#bababa", "values": [{"label":"Drinks", "value":0},\
                                                           {"label":"Rehearsal", "value":0},\
                                                           {"label":"Wedding", "value":0},\
                                                           {"label":"Brunch", "value":0}]}]

    hotels = []
    
    # Calculate Status
    for invite in invites:
        
        for guest in invite.guests:
            
            guest = guest.get()
            
            responses = {"drinks": guest.drinks_rsvp, "rehearsal": guest.rehearsal_rsvp, \
                         "wedding": guest.wedding_rsvp, "brunch":guest.brunch_rsvp}
            
            for guest_response in responses:
                
                if responses[guest_response] == "Will gladly attend":
                    
                    if guest_response == "drinks" and responses["wedding"] == "Will gladly attend":
                        rsvps[0]["values"][0]["value"] += 1
                    elif guest_response =="rehearsal" and responses["wedding"] == "Will gladly attend":
                        rsvps[0]["values"][1]["value"] += 1
                    elif guest_response =="wedding":
                        rsvps[0]["values"][2]["value"] += 1
                    elif guest_response =="brunch" and responses["wedding"] == "Will gladly attend":
                        rsvps[0]["values"][3]["value"] += 1
                    
                elif responses[guest_response] == "Declines with regrets":
                    
                    if guest_response == "drinks":
                        rsvps[1]["values"][0]["value"] += 1
                    elif guest_response =="rehearsal":
                        rsvps[1]["values"][1]["value"] += 1
                    elif guest_response =="wedding":
                        rsvps[1]["values"][2]["value"] += 1
                    elif guest_response =="brunch":
                        rsvps[1]["values"][3]["value"] += 1
                        
                elif responses[guest_response] == "No Response":

                    if guest_response == "drinks":
                        rsvps[2]["values"][0]["value"] += 1
                    elif guest_response =="rehearsal" and invite.rehearsal_invite is True:
                        rsvps[2]["values"][1]["value"] += 1
                    elif guest_response =="wedding":
                        rsvps[2]["values"][2]["value"] += 1
                    elif guest_response =="brunch" and invite.brunch_invite is True:
                        rsvps[2]["values"][3]["value"] += 1                                
    
    return render_template('teamone.html', invites = invites, rsvps = rsvps)
    
@app.route('/add_invitation', methods=['POST'])
def add_invitation():
    
    # Get new invite details
    invite_name = request.form.get("invite_name")
    invite_rehearsal = True if request.form.get("rehearsal") == "on" else False
    invite_brunch = True if request.form.get("brunch") == "on" else False
    
    new_invite = Invite(name = invite_name, rehearsal_invite = invite_rehearsal, brunch_invite = invite_brunch)
    
    raw_guests = [request.form.get("guest_1"), request.form.get("guest_2"), request.form.get("guest_3"), request.form.get("guest_4")]
    new_guests = []
    
    for guest in raw_guests:
        if guest != "":
            new_key = Guest(name = guest).put()
            logging.info(new_key)
            new_guests.append(new_key)
                
    new_invite.guests = new_guests
    new_invite.put()
    
    return redirect(url_for("teamone"))

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for("index"))