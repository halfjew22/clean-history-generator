#!/usr/bin/python

# regex
import re
# executing commands
import subprocess
# arguments
import argparse
# to exit
import sys

def setupTrackingForAllRelevantRemoteBranches(lessonNum=None):
    allRemotes = subprocess.check_output(['git', 'branch', '-a'])
    allRemotes = allRemotes.split(' ')

    if lessonNum is None:
        regexForExerciseOrSolutionBranch = r'(S\d\d\.\d\d-(?:Exercise|Solution)-\w*)'
    elif lessonNum > 9:
        regexForExerciseOrSolutionBranch = r'(T1{}[ab].\d\d-(?:Exercise|Solution)-\w*)'.format(str(lessonNum % 10))
    else:
        regexForExerciseOrSolutionBranch = r'(T\d{}[ab]\.\d\d-(?:Exercise|Solution)-\w*)'.format(str(lessonNum))

    for remote in allRemotes:
        # replace remotes/origin if it's in the string with ''
        if 'remotes/origin/' in remote:
            remote = remote.replace('remotes/origin/', '').strip()
            if re.match(regexForExerciseOrSolutionBranch, remote):
                subprocess.call(['git', 'checkout', remote])
                print 'Checking out {}'.format(remote)


def commitAll(commitMessage):
    print 'Committing ' + commitMessage
    subprocess.call(['git', 'add', '.'])
    subprocess.call(['git', 'commit', '-m', commitMessage])


def status():
    return subprocess.check_output(['git', 'log', '--oneline'])


def gitBranch():
    return subprocess.check_output(['git', 'branch'])


def stapleOnDiff(branchName):

    # Ugly as hell, but gets the job done. Couldn't figure out how to pipe
    cmd = "git diff --binary -R {} | git apply".format(branchName)
    ps = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = ps.communicate()[0]


commit_creator_description = (
    'Create a clean commit history for Sunshine or a Toy App. If no arguments are specified,'
    'a clean commit history of all lessons in Sunshine will be created. Note, that for this'
    ' program to work, branches in the following form must exist:'
    '(S|T)\d\d\.\d\d-(Exercise|Solution)-\w'
)
parser = argparse.ArgumentParser(description=commit_creator_description)
group = parser.add_mutually_exclusive_group()
group.add_argument('-s', '--sunshine',
                   action='store_true',
                   help='Use this flag to create a clean commit history for Sunshine.')
group.add_argument('-t', '--toyapp',
                   action='store_true',
                   help='Use this flag to create a clean commit history for a Toy App. '
                        '(Need to specify a lesson number as well with -l or --lesson.)')
parser.add_argument('-l', '--lesson',
                    help='Which lesson do you want to create a clean commit history for?',
                    type=int)
args = parser.parse_args()
print args.sunshine
print args.toyapp
print args.lesson

lessonNum = args.lesson

if lessonNum:
    print 'Do toy app, lesson ' + str(lessonNum)
    onSunshine = False
else:
    print 'Do all of Sunshine'
    onSunshine = True

# Defining constants
cleanSunshineBranchName = 'sunshine-clean-history'
backupCleanSunshineName = 'BACKUP-' + cleanSunshineBranchName

sunshineCharacter = 'S'

# This lesson number will change, but is constant for testing
cleanToyBranchName = 't{}-clean-history'.format(str(lessonNum))
backupCleanToyBranchName = 'BACKUP-' + cleanToyBranchName

toyAppCharacter = 'T'

branchLeadingChar = sunshineCharacter if onSunshine else toyAppCharacter

setupTrackingForAllRelevantRemoteBranches()
allBranches = gitBranch()

"""
This pattern is a little strange because it contains the ?:
It requires that so I don't have to do any post maintenance to
get he information I want. I just want it to match and not
return the inner group as well. Using the ?: does just that.

Also, I'm using format to pass S or T into the regex depending
on whether we're using this for a [T]oy App or for [S]unshine.
Finally, using format to pass in the lesson number so this will
be somewhat usable for both.
"""
if onSunshine:
    regexForExerciseOrSolutionBranch = r'(S\d\d\.\d\d-(?:Exercise|Solution)-\w*)'
elif lessonNum > 9:
    regexForExerciseOrSolutionBranch = r'(T1{}[ab].\d\d-(?:Exercise|Solution)-\w*)'.format(str(lessonNum % 10))
else:
    regexForExerciseOrSolutionBranch = r'(T\d{}[ab]\.\d\d-(?:Exercise|Solution)-\w*)'.format(str(lessonNum))

cleanCommitBranches = re.findall(regexForExerciseOrSolutionBranch, allBranches)

"""
If we're on Sunshine, we want to do the following:
1) Look for the "sunshine-clean-history" branch.
2) If it exists, rename it to "BACKUP-sunshine-clean
3) Create a new branch sunshine-clean-commit-history (git checkout -b --orphan ....)
4) Ensure the list of cleanCommitBranches are sorted
5) Store the first item of the list in a string (branchName). It is the first branch, the "earliest" branch.
6) Use git diff --binary -R <branchname> | git apply to staple on the changes from the branch in (5)
7) Use git add . to stage the changes for commit
8) Use git commit -m branchName (as your clean branch names should much your intended commit names
9) Repeat (5) - (8) for entire list.
10 Voila
11) Profit?
"""

if onSunshine:
    if cleanSunshineBranchName in allBranches:
        if backupCleanSunshineName in allBranches:
            subprocess.call(['git', 'branch', '-D', backupCleanSunshineName])
        print 'Renaming current clean branch to backup name now...'
        subprocess.call(['git', 'branch', '-m', cleanSunshineBranchName, backupCleanSunshineName])
    subprocess.call(['git', 'checkout', '--orphan', cleanSunshineBranchName])
    cleanCommitBranches.sort()
    for i in range(0, len(cleanCommitBranches)):
        currentBranchName = cleanCommitBranches[i]
        stapleOnDiff(currentBranchName)
        commitAll(currentBranchName)
else:
    # First, check for, and back up (if necessary) the current clean toy branch
    currentToyClean = 't{}-clean-history'.format(lessonNum)
    # If the current toy's branch name already exists, back it up
    if currentToyClean in allBranches:
        print 'Clean history for Lesson ' + str(lessonNum) + ' already exists, renaming now.'
        # If the backup branch already exists, delete it
        currentToyBackup = 'BACKUP-' + currentToyClean
        if currentToyBackup in allBranches:
            # Delete the old backup
            subprocess.call(['git', 'branch', '-D', currentToyBackup])
        # Create the new backup
        subprocess.call(['git', 'branch', '-m', currentToyClean, currentToyBackup])

    # Check for root (common 1st commit for all toy apps)
    if 'root' not in allBranches:
        sys.exit('A common root for all toy apps called \'root\' is required, but was not found. Exiting.')

    print 'Checking out root first to establish common history amongst toy apps'
    subprocess.call(['git', 'checkout', 'root'])
    print 'Checking out new branch: ' + currentToyClean
    subprocess.call(['git', 'checkout', '-b', currentToyClean])

    print 'Now stapling on clean branches for the toy app in lesson ' + str(lessonNum)
    for i in range(0, len(cleanCommitBranches)):
        print 'Current branch in loop: ' + cleanCommitBranches[i]
        stapleOnDiff(cleanCommitBranches[i])
        commitAll(cleanCommitBranches[i])



















