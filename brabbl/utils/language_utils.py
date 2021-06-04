from django.utils import translation
from django.utils.translation import ugettext as _


def set_language(request, lang):
    translation.activate(lang)
    request.LANGUAGE_CODE = translation.get_language()
    return request


def frontend_interface_messages():
    """
    Return list of all frontend's interface messages with translations.
    :return: dict
    """
    return {
        'language': translation.get_language(),
        'translations': {
            "User": _("User"),
            """Thank you for your registration!
            You will receive an email with a confirmation link.
            Once you click this, you can join the discussion.""": _(
                """Thank you for your registration!
                You will receive an email with a confirmation link.
                Once you click this, you can join the discussion."""
            ),
            "sort by date": _("sort by date"),
            "sort by personal review": _("sort by personal review"),
            "sorted by own rating": _(
                "sorted by own rating"
            ),
            "sort by average rating": _("sort by average rating"),
            "You must sign in to participate in the discussion": _(
                "You must sign in to participate in the discussion"
            ),
            "The profile has been updated successfully": _(
                "The profile has been updated successfully"
            ),
            "Choose topic": _("Choose topic"),
            "Profile": _("Profile"),
            "Logout": _("Logout"),
            "Register": _("Register"),
            "Login": _("Login"),
            "You have been logged out": _("You have been logged out"),
            "Come back soon!": _("Come back soon!"),
            "All discussions": _("All discussions"),
            "The argument has been changed": _(
                "The argument has been changed"
            ),
            "Great! Your argument is online now": _(
                "Great! Your argument is online now"
            ),
            "Edit discussion": _("Edit discussion"),
            "Edit Discussion": _("Edit Discussion"),
            "Create discussion": _("Create discussion"),
            "An email was sent with instructions on how to reset the password": _(
                "An email was sent with instructions on how to reset the password"
            ),
            "Edit suggestion": _("Edit suggestion"),
            "Report suggestion": _("Report suggestion"),
            "Add new suggestion": _("Add new suggestion"),
            "Add new Discussion": _("Add new Discussion"),
            "Add new Survey": _("Add new Survey"),
            "Update Discussion": _("Update Discussion"),
            "Add new pro-argument": _("Add new pro-argument"),
            "Add new contra-argument": _("Add new contra-argument"),
            "Edit argument": _("Edit argument"),
            "Publish argument": _("Publish argument"),
            "Publish Argument": _("Publish Argument"),
            "Edit survey": _("Edit survey"),
            "Edit Survey": _("Edit Survey"),
            "Add new survey": _("Add new survey"),
            "Survey": _("Survey"),
            "Discussion": _("Discussion"),
            "Tags": _("Tags"),
            "Settings": _("Settings"),
            "Create a new account": _("Create a new account"),
            "Forgot your password?": _("Forgot your password?"),
            "Please drag a picture to the image area to change your profile picture": _(
                "Please drag a picture to the image area to change your profile picture"
            ),
            "Please drag a picture to the image area to change discussion picture": _(
                "Please drag a picture to the image area to change discussion picture"
            ),
            "Reset Password": _("Reset Password"),
            "Update profile": _("Update profile"),
            "Already have an account?": _("Already have an account?"),
            "to": _("to"),
            "from": _("from"),
            "Edit": _("Edit"),
            "Add new": _("Add new"),
            "Cancel": _("Cancel"),
            "There was a server error": _("There was a server error"),
            "The action could not be carried out": _("The action could not be carried out"),
            "Please provide a subject": _("Please provide a subject"),
            "Please provide details for your argument": _(
                "Please provide details for your argument"
            ),
            "Just arguments": _("Just arguments"),
            "Just the Opiniometer": _("Just the Opiniometer"),
            "Opiniometer plus Arguments": _("Opiniometer plus Arguments"),
            "Thesis statement or question": _("Thesis statement or question"),
            "Please provide a thesis statement or question": _(
                "Please provide a thesis statement or question"
            ),
            "The thesis statement / question must not exceed 160 characters": _(
                "The thesis statement / question must not exceed 160 characters"
            ),
            "Please select the type of discussion": _(
                "Please select the type of discussion"
            ),
            "Please select the Opiniometer": _(
                "Please select the Opiniometer"
            ),
            "Please select the type of Opiniometer": _(
                "Please select the type of Opiniometer"
            ),
            "Allow suggestions by admins only": _(
                "Allow suggestions by admins only"
            ),
            "Allow suggestions by users": _("Allow suggestions by users"),
            "Please provide a (unique) username": _(
                "Please provide a (unique) username"
            ),
            "Please provide a password": _("Please provide a password"),
            "Please provide a fist name": _("Please provide a fist name"),
            "Please provide a last name": _("Please provide a last name"),
            "Please provide an email address": _(
                "Please provide an email address"
            ),
            "Please provide a valid email address": _(
                "Please provide a valid email address"
            ),
            "No email notifications": _("No email notifications"),
            "News e-mail (frequency)": _("News e-mail (frequency)"),
            "daily": _("daily"),
            "weekly": _("weekly"),
            "User name": _("User name"),
            "First name": _("First name"),
            "Last name": _("Last name"),
            "Email Address": _("Email Address"),
            "The passwords do not match": _("The passwords do not match"),
            "Password": _("Password"),
            "Please enter a password again": _(
                "Please enter a password again"
            ),
            "characters remaining": _("characters remaining"),
            "Average opinion": _("Average opinion"),
            "What do you think?": _("What do you think?"),
            "Argument": _("Argument"),
            "Reply": _("Reply"),
            "Replies": _("Replies"),
            "No suggestions yet": _("No suggestions yet"),
            "Thanks for reporting! We will review that content shortly": _(
                "Thanks for reporting! We will review that content shortly"
            ),
            "Thank you for your message": _("Thank you for your message"),
            "We will consider the amount shortly": _("We will consider the amount shortly"),
            "Hide proposal": _("Hide proposal"),
            "Edit proposal": _("Edit proposal"),
            "Report proposal": _("Report proposal"),
            "Add new argument": _("Add new argument"),
            "No arguments yet": _("No arguments yet"),
            "Start the discussion now!": _(" Start the discussion now!"),
            "Show more arguments": _("Show more arguments"),
            "Contra-Argument": _("Contra-Argument"),
            "Pro-Argument": _("Pro-Argument"),
            "Hide argument": _("Hide argument"),
            "Show argument": _("Show argument"),
            "Delete argument": _("Delete argument"),
            "Report argument": _("Report argument"),
            "Rate": _("Rate"),
            "powered by": _("powered by"),
            "DISCUSSION": _("DISCUSSION"),
            "inconsequential": _("inconsequential"),
            "questionable": _("questionable"),
            "justifiable": _("justifiable"),
            "relevant": _("relevant"),
            "convincingly": _("convincingly"),
            "Contra": _("Contra"),
            "Pro": _("Pro"),
            "Votes": _("Votes"),
            "Profile picture": _("Profile picture"),
            "Back": _("Back"),
            "cancel": _("cancel"),
            "create": _("create"),
            "change": _("change"),
            "Opinion": _("Opinion"),
            "Subject": _("Subject"),
            "Suggestion": _("Suggestion"),
            "Please enter a suggestion": _("Please enter a suggestion"),
            "by": _("by"),
            "All": _("All"),
            "Total": _("Total"),
            "Active": _("Active"),
            "Not Active": _("Not Active"),
            "Filter by status": _("Filter by status"),
            "Completed": _("Completed"),
            "Starts in": _("Starts in"),
            "Ends in": _("Ends in"),
            "Starts": _("Starts"),
            "Finishes": _("Finishes"),
            "d": _("d"),
            "h": _("h"),
            "m": _("m"),
            "s": _("s"),
            "Start Time": _("Start Time"),
            "End Time": _("End Time"),
            "Answer(s)": _("Answer(s)"),
            "very poor": _("very poor"),
            "poor": _("poor"),
            "ok": _("ok"),
            "good": _("good"),
            "very good": _("very good"),
            "CONTRA": _("CONTRA"),
            "PRO": _("PRO"),
            "Statement": _("Statement"),
            "Statements": _("Statements"),
            "Write new statement": _("Write new statement"),
            "Write new argument": _("Write new argument"),
            "Login with Facebook": _("Login with Facebook"),
            "Login with Twitter": _("Login with Twitter"),
            "Login with Google": _("Login with Google"),
            "Sign up with": _("Sign up with"),
            "Sign In": _("Sign In"),
            "or via mail": _("or via mail"),
            "Login to participate": _("Login to participate"),
            "Year of Birth": _("Year of Birth"),
            "Please provide a years of birth": _("Please provide a years of birth"),
            "Gender": _("Gender"),
            "Whatever": _("Whatever"),
            "Male": _("Male"),
            "Female": _("Female"),
            "Please provide a gender": _("Please provide a gender"),
            "Postcode": _("Postcode"),
            "Please provide a postcode": _("Please provide a postcode"),
            "Country": _("Country"),
            "Please provide a country": _("Please provide a country"),
            "City": _("City"),
            "Please provide a city": _("Please provide a city"),
            "Organization": _("Organization"),
            "Please provide a organization": _("Please provide a organization"),
            "Position": _("Position"),
            "Please provide a position": _("Please provide a position"),
            "Bundesland": _("Bundesland"),
            "Please provide a bundesland": _("Please provide a bundesland"),
            "Edit List": _("Edit List"),
            "Discussion List": _("Discussion List"),
            "Save List": _("Save List"),
            "Show all": _("Show all"),
            "Show sum of tags": _("Show sum of tags"),
            "Show intersection of tags": _("Show intersection of tags"),
            "List name": _("List name"),
            "Hide tag filter for Users": _("Hide tag filter for Users"),
            "Tag filter in the list view will not be shown to users": _(
                "Tag filter in the list view will not be shown to users"),
            "Please provide a list name": _("Please provide a list name"),
            "The list name must not exceed 160 characters": _("The list name must not exceed 160 characters"),
            "Content of list": _("Content of list"),
            "Please select the content of list": _("Please select the content of list"),
            "Please select the Wording schema": _("Please select the Wording schema"),
            "You can enter maximum of 4 digits": _("You can enter maximum of 4 digits"),
            "Add a tag": _("Add a tag"),
            "Press enter to add a tag": _("Press enter to add a tag"),
            "The discussion has not started yet": _("The discussion has not started yet"),
            "Write Pro-Argument": _("Write Pro-Argument"),
            "Write Contra-Argument": _("Write Contra-Argument"),
            "Update Argument": _("Update Argument"),
            "They were an email sent with instructions to reset the password":
                _("They were an email sent with instructions to reset the password"),
            "Add media": _("Add media"),
            "User list": _("User list"),
            "You can also upload an image or add a Youtube link": _(
                "You can also upload an image or add a Youtube link"),
            "Image": _("Image"),
            "Content removed": _("Content removed"),
            "This content was inappropriate and has been removed by our staff": _(
                "This content was inappropriate and has been removed by our staff"),
            "Please stick to our guidelines for good discussions and refrain from posts that are likely to be regarded "
            "as offensive or rude": _(
                "Please stick to our guidelines for good discussions and refrain from posts that are likely to be"
                " regarded as offensive or rude"),
            "User can add replies to arguments": _("User can add replies to arguments"),
            "Allow replies to arguments": _("Allow replies to arguments"),
            "Delete discussion": _("Delete discussion"),
            "Really delete this discussion? (This cannot be undone!)": _(
                "Really delete this discussion? (This cannot be undone!)"),
        }
    }
