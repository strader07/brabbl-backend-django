# brabbl

## Development

* Go to project folder
* `virtualenv -p /usr/bin/python3 env`
* `. env/bin/activate`
* `pip install -e .`
* `pip install -r requirements/dev.txt`
* `cd brabbl`
* `python manage.py migrate --settings=brabbl.conf.dev`
* `python manage.py runserver --settings=brabbl.conf.dev`

CSS files for Welcome page are got from the frontend application considering selected theme. Please run `npm run build_staging` to generate theme files.
Also don't forget to run `python manage.py collectstatic`


## Deployment:

Check if staging or production server have newest translations using `git status`.

Copy it to your local machine using `scp` if need. For example:

`scp brabbl-staging@api.brabbl.com://home/brabbl-staging/src/brabbl/brabbl/locale/de/LC_MESSAGES/django.po ./Python/brabbl/django.po`

If translations aren't up to date just revert changes using `git checkout <path to file>`

Run deploying script

* `fab staging deploy` or `fab production deploy`

For provisioning of server, check the `deployment/` subdirectory.

Be sure that your host is added into `ALLOWED_HOSTS`. Fill in `SITE_DOMAIN` on your settings.

**Be attention** `SESSION_COOKIE_SECURE` setted as `True`. So if you don't use SSL you should set it to `Fasle`

## API Docs

The current API is documented (as API Blueprint) in the docs folder.
Use `npm install` and `gulp` in the docs folder to build a html version of the docs.


## Coding Style

Make sure your editor of choice supports EditorConfig [http://editorconfig.org] so the
styles defined in `.editorconfig` are picked up and respected.

PEP8 conformity is checked as part of the test suite.


## Testing

Use `py.test brabbl` from the project root to run the tests.


## Embedding options

brabbl API can be integrated as a list page (listing all discussions for
a specific customer) or on a detail page (hosting the actual discussions).

For integration on a detail page, a customer's staff needs to activate
discussions on that specific page and select one of *five* options for
integration:

1. Only barometer
2. Only arguments
3. Barometer and arguments
4. List of user-provided answers (only barometer)
5. List of user-provided answers (barometer and arguments)

If discussion hasn't created yet, staff members can login on the list page.


## Snippet

```
<div id="brabbl-widget"></div>
<script>
(function() {
  window.brabbl = {
    customerId: "brabbl-test",
    /* id for article: e.g. a context var filled in by the customer or something
	   like `window.location.pathname`  */
    articleId: "XYZ",
    defaultTags: ["foo", "bar"], // this tags will be added automatically on "Create discussion form"
    view: "list" // only required for list view.
  },
  script = document.createElement('script'),
  entry = document.getElementsByTagName('script')[0];
  script.src = "http://staging.api.brabbl.com/embed/brabbl.js";
  script.async = true;
  entry.parentNode.insertBefore(script, entry);
})();
</script>
```

## Glossary

* Customer - one "integration environment". All users are specific to
  one customer (although usernames must be unique through all customers).
  Integrations are limited to certain domains per customer.

* Discussion - is created as soon as a staff member activates brabbl on
  a certain article page. Requires a unique ID from the hosting CMS.

* Statement - parent for all arguments. Discussions can have _one_ statement
  attached (for integration options 1-3) or _multiple_ statements (for 4 and 5).
