# target-finder

TO DO:
- Trello.com is in bugcrowd and in scope but targets from scan don't pass check because not *.trello.com, bounty program is just trello.com so should we assume anything in domain is automatically in-scope?
- add test to see if targets return http status code of 200? can implement this as an option
- Entrust or APIs instead of crt.sh?
- should we scan the Common Names instead of the Matching Identities?
- MIT License?

FUTURE:
- Add HackerOne and other bug bounty program databases
- source for bugbounty db is not updated fast enough (i.e. gap.com is not there). gather in scope targets using APIs?
https://docs.bugcrowd.com/api/getting-started/
https://docs.bugcrowd.com/api/2021-10-28/#tag/program_resource/operation/getProgram
