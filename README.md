# StudyMate

StudyMate is a web app that helps female university students form study groups by course.
It is built with HTML, CSS, JavaScript and Firebase (Authentication + Cloud Firestore), with no other library.

CS 388T - Agile Software Development, Section 7C6.
Team: Haneen Aljumah (445008652), Noha Alqahtani (445008650), Moudhi Aldakhil (445008789), Renad Al-aqili (445008840).

## Repository

https://github.com/Studymate-projectG/StudyMate (branch `main`)

## Features

Sprint 1 (US1 to US5):

1. Sign up and log in with a university email.
2. Create and edit the profile (major and courses).
3. Create a study group with a title, course, description, maximum members and meeting time.
4. Browse the groups and filter them by course code.
5. Join a group that has a free seat (no double join, no join when the group is full).

Sprint 2 (US6, US7, US8, US9, US10, US11, US17):

6. View the members of a group and remove a member (leader only).
7. My Groups page with the groups the student created and the groups she joined.
8. Edit the group information or close the group (leader only).
9. Post announcements inside the group (leader only, members read them).
10. Leave a group (members only, the seat becomes free again).
11. In-app reminder when the session starts within the next 24 hours.
17. A meeting time in the past is refused when a group is created or edited.

Not implemented in this increment: item 18 (approval of a new account by the female campus administration) is on hold
because the approval process is not defined yet, and item 19 (reset the password by email) needs a real Firebase project.

## Files

| File | What it does |
|------|--------------|
| index.html, js/lg.js | Log in page |
| signup.html, js/su.js | Sign up page |
| profile.html, js/pf.js | My profile (major and courses) |
| groups.html, js/gl.js | Groups list, course filter, closed groups hidden, reminder banner |
| create.html, js/cg.js | Create group form (with the future-time check) |
| group.html, js/gd.js | Group details, join, leave, members, remove, close, announcements, reminder |
| mine.html, js/my.js | My Groups page |
| edit.html, js/ed.js | Edit group form |
| js/ap.js | Shared code (Firebase start, messages, login check, reminder helpers) |
| js/cfg.js | Firebase settings and the university email domain |
| js/cr.js | Courses list |
| css/st.css | Styles |
| firestore.rules | Firebase security rules |
| firebase.json, .firebaserc | Emulator and hosting settings |
| tests/e2e.py | Sprint 1 acceptance and regression tests (34 checks) |
| tests/p3.py | Sprint 2 tests (58 checks) |
| tests/full_flow.py | The 13-step journey test (15 checks) |
| tests/rules.test.mjs | Firestore security rules tests (49 checks) |
| tests/evidence_chrome.py | Chrome screenshots of every story |
| tests/evidence_vscode_term.py | Screenshots of the editor and the test terminal |
| tests/demo.sh | Runs the four suites in order |

## Option A - Run on your laptop with the Firebase Emulator (no Firebase account needed)

You need Node.js 18 or newer and Java 11 or newer.

```
cd 08_StudyMate_App
npm install
npx firebase-tools@13 emulators:start --project demo-studymate
```

Open http://localhost:5000 in the browser. The data is only kept while the emulator is running.
The emulator page at http://localhost:4000 shows the saved users, groups, members and announcements.
Sign up with an email that ends with `@university.edu.sa` (for example `sara@university.edu.sa`).

## Option B - Run with a real Firebase project

1. Create a project in https://console.firebase.google.com
2. Authentication > Sign-in method > enable Email/Password.
3. Firestore Database > create database.
4. Project settings > Your apps > add a Web app and copy the config.
5. In js/cfg.js paste the config into `cfg`. The app uses the emulator only when it runs on localhost, so nothing else changes.
6. Deploy the rules and the site:

```
npx firebase-tools@13 login
npx firebase-tools@13 use --add
npx firebase-tools@13 deploy
```

## University email domain

The allowed domain is set in two places and they must match:

- js/cfg.js: `const dom = "@university.edu.sa";`
- firestore.rules: `matches('.*@university[.]edu[.]sa$')`

The domain is a placeholder because the real domain of the university has not been confirmed for this project.
To use another domain, change both places.

## Run the tests

The tests use the Firebase Emulator only. Do not run them against a real Firebase project, because the test clears
the users and the groups before it starts.

1. Start the emulator (Option A) and keep it running.
2. Install the test tools:

```
pip install playwright
python -m playwright install chromium
npm install
```

3. Run everything with one command (about 5 minutes):

```
cd 08_StudyMate_App
mkdir -p shots
bash tests/demo.sh
```

`tests/demo.sh` runs the four suites in this order and prints one summary line for each of them:

| Suite | File | Checks |
|-------|------|--------|
| Firestore security rules (Emulator) | tests/rules.test.mjs | 49 |
| Sprint 1 regression tests (Chrome) | tests/e2e.py | 34 |
| Sprint 2 tests | tests/p3.py | 58 |
| Full journey (13 steps) | tests/full_flow.py | 15 |

The final test suite includes 156 checks (49 security rules, 34 Sprint 1 regression, 58 Sprint 2, and 15 full-journey checks). The earlier 8 November run of 139 checks is archived in `Evidence/Test_Logs/run_all.log`.

If the rules test cannot reach the emulator from your terminal, run it with the address of the emulator
(for example `FSHOST=127.0.0.1 node tests/rules.test.mjs`).

The screenshots of the Chrome walkthrough are made with:

```
mkdir -p shots
python tests/evidence_chrome.py
```

They are written to `../Evidence/Screenshots` (the folder path can be changed with the `SHOTDIR` variable).

## Notes and limits

- The session reminder is inside the app only. Push notifications and email notifications are not part of this sprint;
  they need a notification service and they are written as item 22 in the Product Backlog.
- The application was tested on the Firebase Emulator with the demo configuration; it has not been deployed to a real
  Firebase project (no production Firebase project is used in this course).
- Closed groups are not deleted. They stay in the database with `closed: true` and hidden from the lists, so the leader
  can still open the group page from My Groups.
