from pathlib import Path
import os
import numpy as np
import app.osutils as osutils
from app.config import config
from app.logger.loggingHelper import loggingHelper
from app.exceptions import GitError, NoSuchFileError
from app.jira import jira
import re
jiraIssueKeyRegex = re.compile(r"[a-zA-Z]+-\d+")

logger = loggingHelper.getLogger(__name__)

class BranchName():

    branchType = ''
    shortName = ''

    def __init__(self, branchType, shortName):
        self.branchType = branchType
        self.shortName = shortName

# feature/7.3_[A-Z]_BSST-xxxxx_[short_desc]
class FeatureBranchName():

    branchType = ''
    version = ''
    team = ''
    jiraIssueKey = ''
    description = ''
    shortName = ''

    def __init__(self, strName):
        branch = strName.split('/')
        self.branchType = branch[0] # feature or bugfixing
        self.shortName = branch[1]
        branch = branch[1].split('_')
        self.version = branch[0]
        result = jiraIssueKeyRegex.search(branch[1])
        if result:
            self.jiraIssueKey = branch[1]
            if len(branch) > 2:
                self.description = branch[2]
        else:
            self.team = branch[1]
            self.jiraIssueKey = branch[2]
            if len(branch) > 3:
                self.description = branch[3]

# team/7.3_TEAM
class TeamBranchName():

    branchType = ''
    version = ''
    team = ''
    shortName = ''

    def __init__(self, strName):
        branch = strName.split('/')
        self.branchType = branch[0] # team
        self.shortName = branch[1]
        branch = branch[1].split('_')
        self.version = branch[0]
        self.team = branch[1]

def branchNameFromString(branch):
    if branch.startswith('feature/') or branch.startswith('bugfixing/'):
        return FeatureBranchName(branch)
    elif branch.startswith('team/'):
        return TeamBranchName(branch)
    else:
        return BranchName('', branch)

class _Repository():

    def __init__(self, name, path):
        confSubData = config["git"][name]
        self.name = name
        self.path = path
        self.stable = confSubData["stable"]

    def checkIfBranchExists(self, branch):
        raise NotImplementedError("Please Implement this method")

    def checkIfStableMergedTobranch(self, branch):
        raise NotImplementedError("Please Implement this method")

    def clean(self):
        cmd = (
            'cd {local_repository_path} && '
            'git clean -x -d --force'
        ).format(**{
            'local_repository_path': self.path
        })
        logger.debug('Executing git cmd: ' + cmd)
        out = osutils.osCmdToString(cmd)
        if out[2] != 0:
            logger.debug("GIT cmd out: " + str(out[0]))
            logger.debug("GIT cmd err: " + str(out[1]))
            logger.debug("GIT cmd exit code: " + str(out[2]))
            raise GitError("Can't clean repository: " + self.path, repository=self.name)

    def abortMerge(self, quietly=False):
        cmd = (
            'cd {local_repository_path} && '
            '(git merge --abort'
            '{quietly})'
        ).format(**{
            'local_repository_path': self.path,
            'quietly': ('' if quietly else ' && exit 0 || exit 0')
        })
        logger.debug('Executing git cmd: ' + cmd)
        out = osutils.osCmdToString(cmd)
        if out[2] != 0:
            logger.debug("GIT cmd out: " + str(out[0]))
            logger.debug("GIT cmd err: " + str(out[1]))
            logger.debug("GIT cmd exit code: " + str(out[2]))
            raise GitError("Can't abort merge: " + self.path, repository=self.name)

    def abort_merge(self, quietly=False):
        cmd = (
            f'cd {self.path} && '
            f'git merge --abort'
        )
        logger.debug(f'Executing git cmd: {cmd}')
        stdout, stderr, exitcode = osutils.osCmdToString(cmd)
        if exitcode != 0 and not quietly:
            logger.debug(f"GIT cmd out: {stdout}")
            logger.debug(f"GIT cmd err: {stderr}")
            logger.debug(f"GIT cmd exit code: {exitcode!s}")
            raise GitError("Can't abort merge: " + self.path, repository=self.name)

    def resetRepository(self, checkoutBranch=None):
        cmd = (
            'cd {local_repository_path} && '
            'git fetch --prune --all && ' # zaciagniecie najnowszych zmian ze zdalnego repo + usuniecie nieistniejacych juz referencji/branchy
            '(git merge --abort && exit 0 || exit 0) && ' # abort procesu mergowania (bez raportowania bledu za pomoca exit code != 0)
            'git clean -x -d --force && ' # usuwanie plikow, ktore nie sa zaewidencjonowane w repozytorium
            'git reset --hard HEAD && ' # zresetowanie repozytorium do commita wskazanego przez HEAD
            '{checkout_branch}' # opcjonalnie checkout brancha do jakiego chcemy zresetowac repozytorium
            'git reset --hard @{{upstream}} && ' # zresetowanie repozytorium do ostatniego commita z upstream (odpowiednik brancha lokalnego po stronie zdalnego repo)
            'git pull --all' # odswiezenie najnowszych zmian ze zdalnego repo
        ).format(**{
            'local_repository_path': self.path,
            'checkout_branch': ('' if not checkoutBranch else 'git checkout {0} && '.format(checkoutBranch))
        })
        logger.debug('Executing git cmd: ' + cmd)
        out = osutils.osCmdToString(cmd)
        if out[2] != 0:
            logger.debug("GIT cmd out: " + str(out[0]))
            logger.debug("GIT cmd err: " + str(out[1]))
            logger.debug("GIT cmd exit code: " + str(out[2]))
            raise GitError("Can't reset repository: " + self.path, repository=self.name)

    def checkout(self, hash):
        cmd = (
            'cd {local_repository_path} && '
            'git checkout "{hash}"'
        ).format(**{
            'local_repository_path': self.path,
            'hash': hash
        })
        logger.debug('Executing git cmd: ' + cmd)
        out = osutils.osCmdToString(cmd)
        if out[2] != 0:
            logger.debug("GIT cmd out: " + str(out[0]))
            logger.debug("GIT cmd err: " + str(out[1]))
            logger.debug("GIT cmd exit code: " + str(out[2]))
            raise GitError("Can't checkout hash {0}".format(hash), repository=self.name)
        return self

    def checkoutRc(self):
        return self.checkout(self.rc)

    def checkoutFb(self, mergeRequest):
        return self.checkout(mergeRequest.getBranchName())

    def checkout_fb_or_stable(self, mergeRequest):
        if self.checkIfBranchExists(mergeRequest.getBranchName()):
            return self.checkout(mergeRequest.getBranchName())
        else:
            return self.checkout_stable()

    def checkout_stable(self):
        return self.checkout(self.stable)

    def checkoutMaster(self):
        return self.checkout('master')

    def getHead(self):
        cmd = (
            'cd {local_repository_path} && '
            'git rev-parse HEAD'
        ).format(**{
            'local_repository_path': self.path
        })
        logger.debug('Executing git cmd: ' + cmd)
        out = osutils.osCmdToString(cmd)
        if out[2] != 0:
            logger.debug("GIT cmd out: " + str(out[0]))
            logger.debug("GIT cmd err: " + str(out[1]))
            logger.debug("GIT cmd exit code: " + str(out[2]))
            raise GitError("Can't get HEAD from current branch".format(hash), repository=self.name)
        return out[0]

    def pull(self):
        cmd = (
            'cd {local_repository_path} && '
            'git pull'
        ).format(**{
            'local_repository_path': self.path
        })
        logger.debug('Executing git cmd: ' + cmd)
        out = osutils.osCmdToString(cmd)
        if out[2] != 0:
            logger.debug("GIT cmd out: " + str(out[0]))
            logger.debug("GIT cmd err: " + str(out[1]))
            logger.debug("GIT cmd exit code: " + str(out[2]))
            raise GitError("Can't pull repository " + self.name)
        return self

    def addAllCommitAndPush(self, msg):
        cmd = (
            'cd {local_repository_path} && '
            'git add -A && '
            'git diff-index --quiet HEAD || '
            '(git commit -m "{msg}" && '
            'git pull && '
            'git push)'
        ).format(**{
            'local_repository_path': self.path,
            'msg': msg
        })
        logger.debug('Executing git cmd: ' + cmd)
        out = osutils.osCmdToString(cmd)
        if out[2] != 0:
            logger.debug("GIT cmd out: " + str(out[0]))
            logger.debug("GIT cmd err: " + str(out[1]))
            logger.debug("GIT cmd exit code: " + str(out[2]))
            raise GitError("Can't commit and push to repository {0}\nstdout: {1}\nstderr: {2}".format(self.name, str(out[0]), str(out[1])), repository=self.name)
        return self

    def logAllCommitsInRefAndPath(self, refA, onlyInPath):
        cmd = (
            'cd {local_repository_path} && '
            'git log --format="%H||%s" --no-merges origin/{refA} -- {onlyInPath}'
        ).format(**{
            'local_repository_path': self.path,
            'refA': refA,
            'onlyInPath': onlyInPath
        })
        logger.debug('Executing git cmd: ' + cmd)
        out = osutils.osCmdToString(cmd)
        if out[2] != 0:
            logger.debug("GIT cmd out: " + str(out[0]))
            logger.debug("GIT cmd err: " + str(out[1]))
            logger.debug("GIT cmd exit code: " + str(out[2]))
            raise GitError('Can\'t log commits in repository {0} in branch {1} and path "{2}" \nStdout: {3}\nStderr: {4}'.format(self.name, refA, onlyInPath, str(out[0]), str(out[1])), repository=self.name)
        commits = []
        if out[0]:
            commits = out[0].split('\n')
            commits = [commit.split('||') for commit in commits]
        return commits

    def logCommitsBetweenTwoRefs(self, refA, refB, onlyInPath=None):
        cmd = (
            'cd {local_repository_path} && '
            'git log --format="%H||%s" --no-merges origin/{refA}..origin/{refB}' # Commits that are in B and not in A
        ).format(**{
            'local_repository_path': self.path,
            'refA': refA,
            'refB': refB
        })
        if onlyInPath:
            cmd = cmd + ' -- ' + onlyInPath
        logger.debug('Executing git cmd: ' + cmd)
        out = osutils.osCmdToString(cmd)
        if out[2] != 0:
            logger.debug("GIT cmd out: " + str(out[0]))
            logger.debug("GIT cmd err: " + str(out[1]))
            logger.debug("GIT cmd exit code: " + str(out[2]))
            raise GitError("Can't log commits between two references in repository {0}\nStdout: {1}\nStderr: {2}".format(self.name, str(out[0]), str(out[1])), repository=self.name)
        commits = []
        if out[0]:
            commits = out[0].split('\n')
            commits = [commit.split('||') for commit in commits]
        return commits

    def fetch_branch(self, branch_name):
        cmd = (
            'cd {local_repository_path} && '
            'git fetch origin "refs/heads/{branch_name}"'
        ).format(**{
            'local_repository_path': self.path,
            'branch_name': branch_name
        })
        logger.debug('Executing git cmd: ' + cmd)
        out = osutils.osCmdToString(cmd)
        if out[2] != 0:
            logger.debug("GIT cmd out: " + str(out[0]))
            logger.debug("GIT cmd err: " + str(out[1]))
            logger.debug("GIT cmd exit code: " + str(out[2]))
            raise GitError("Can't fetch branch {0} in repository {1}\nStdout: {2}\nStderr: {3}".format(branch_name, self.name, str(out[0]), str(out[1])), repository=self.name)
        return self

    def logCommitsBetweenFBAndStable(self, mergeRequest):
        fbName = mergeRequest.getBranchName()
        if self.checkIfBranchExists(fbName):
            return (self
                    .fetch_branch(self.stable)
                    .fetch_branch(fbName)
                    .logCommitsBetweenTwoRefs(self.stable, fbName))
        else:
            return []

    def cloneBranch(self, targetBranch, sourceBranch):
        """Create new branch with name targetBranch as a clone of branch sourceBranch.

        Keyword arguments:
        targetBranch -- branch to create
        sourceBranch -- branch to be cloned
        """

        if self.checkIfBranchExists(sourceBranch):
            self.checkout(sourceBranch).pull()
            cmd = (
                'cd {local_repository_path} && '
                'git checkout -b "{target_branch}" "{source_branch}" && '
                'git push --set-upstream origin "{target_branch}"'
            ).format(**{
                'local_repository_path': self.path,
                'target_branch': targetBranch,
                'source_branch': sourceBranch
            })
            logger.debug('Executing git cmd: ' + cmd)
            out = osutils.osCmdToString(cmd)
            if out[2] != 0:
                logger.debug("GIT cmd out: " + str(out[0]))
                logger.debug("GIT cmd err: " + str(out[1]))
                logger.debug("GIT cmd exit code: " + str(out[2]))
                raise GitError('Can\'t clone branch "{0}" into "{1}"'.format(sourceBranch, targetBranch))
        else:
            logger.debug('Source branch "{0}" not found. Nothing to clone'.format(sourceBranch))
        return self

    def is_merge_in_progress(self):
        cmd = (
            f'cd {self.path} && '
            f'git merge HEAD'
        )
        logger.debug(f'Executing git cmd: {cmd}')
        stdout, stderr, exitcode = osutils.osCmdToString(cmd)
        if exitcode == 128:
            return True
        elif exitcode == 0:
            return False
        else:
            logger.debug(f"GIT cmd out: {stdout}")
            logger.debug(f"GIT cmd err: {stderr}")
            logger.debug(f"GIT cmd exit code: {exitcode!s}")
            raise GitError("Can't check if merging in progress")


class _BranchTypeRepository(_Repository):

    def checkIfBranchExists(self, branch):
        cmd = (
            'cd {local_repository_path} && '
            'git ls-remote --heads --exit-code origin "refs/heads/{branch}"'
        ).format(**{
            'local_repository_path': self.path,
            'branch': branch
        })
        logger.debug('Executing git cmd: ' + cmd)
        out = osutils.osCmdToString(cmd)
        if out[2] == 0:
            logger.debug("Branch {0} found in repository {1}".format(branch, self.name))
            return True
        else:
            logger.debug("Branch {0} not found in repository {1}".format(branch, self.name))
            return False

    def mergeBranches(self, jiraID, branchFrom, branchTo):
        cmd = (
            'cd {local_repository_path} && '
            'git checkout {branchTo} && '
            'git pull && '
            'git fetch origin refs/heads/{branchFrom} && '
            'git merge origin/{branchFrom} -m "Merge request: {jiraID}. Mergowanie: origin/{branchFrom} -> {branchTo}" && '
            'git push'
        ).format(**{
            'local_repository_path': self.path,
            'branchFrom': branchFrom,
            'branchTo': branchTo,
            'jiraID': jiraID
        })
        logger.debug('Executing git cmd: ' + cmd)
        out = osutils.osCmdToString(cmd)
        if out[2] != 0:
            get_list_of_conflict_files = (
                'cd {local_repository_path} && '
                'git diff --name-only --diff-filter=U '
            ).format(**{
                'local_repository_path': self.path
            })
            logger.debug('Executing git cmd: ' + get_list_of_conflict_files)
            conflict = osutils.osCmdToString(get_list_of_conflict_files)

            if self.is_merge_in_progress() and conflict[2] == 0 and conflict[0]:
                raise GitError("List of conflicts:\n{}".format(conflict[0]))
            else:
                logger.debug("GIT cmd out: " + str(out[0]))
                logger.debug("GIT cmd err: " + str(out[1]))
                logger.debug("GIT cmd exit code: " + str(out[2]))
                raise GitError("Can't merge branch {0} into branch {1} in repository {2}\nStdout: {3}\nStderr: {4}".format(branchFrom, branchTo, self.name, str(out[0]), str(out[1])), repository=self.name)

    def merge_branches_no_commit(self, branch_from, branch_to):
        cmd = (
            f'cd {self.path} && '
            f'git checkout {branch_to} && '
            f'git pull && '
            f'git fetch origin refs/heads/{branch_from} && '
            f'git merge --no-commit origin/{branch_from}'
        )
        logger.debug(f'Executing git cmd: {cmd}')
        stdout, stderr, exitcode = osutils.osCmdToString(cmd)
        if exitcode != 0:
            logger.debug(f"GIT cmd out: {stdout}")
            logger.debug(f"GIT cmd err: {stderr}")
            logger.debug(f"GIT cmd exit code: {exitcode!s}")
            raise GitError((
                f"Can't merge branch {branch_from!s} into branch {branch_to!s} in repository {self.name!s}\n"
                f"Stdout: {stdout!s}\n"
                f"Stderr: {stderr!s}"
            ))

    def mergeStableToFb(self, mergeRequest, nocommit=False):
        if self.checkIfBranchExists(mergeRequest.getBranchName()):
            if nocommit:
                self.merge_branches_no_commit(self.stable, mergeRequest.getBranchName())
            else:
                self.mergeBranches(mergeRequest.getJiraID(), self.stable, mergeRequest.getBranchName())

    def mergeFbToStable(self, mergeRequest):
        if self.checkIfBranchExists(mergeRequest.getBranchName()):
            self.mergeBranches(mergeRequest.getJiraID(), mergeRequest.getBranchName(), self.stable)


class Git:

    def __init__(self, rootPath):
        self.repositories = dict()
        self.repositories["bss"] = _BranchTypeRepository('bss', os.path.normpath(os.path.join(rootPath, config["git"]["bss_dir"])))
        self.repositories["tum"] = _BranchTypeRepository('tum', os.path.normpath(os.path.join(rootPath, config["git"]["tum_dir"])))

    def checkIfBranchExists(self, branch):
        exists = dict()
        exists["bss"] = self.repositories["bss"].checkIfBranchExists(branch)
        exists["tum"] = self.repositories["tum"].checkIfBranchExists(branch)
        return any(exists.values()), exists

    def resetRepositories(self, checkoutBranch=None):
        for repository in self.repositories:
            self.repositories[repository].resetRepository(checkoutBranch)

    def mergeStableToFb(self, mergeRequest, nocommit=False):
        for repository in self.repositories:
            self.repositories[repository].mergeStableToFb(mergeRequest, nocommit=nocommit)
        return self

    def mergeFbToStable(self, mergeRequest):
        for repository in self.repositories:
            self.repositories[repository].mergeFbToStable(mergeRequest)
        return self

    def checkoutFbAndPull(self, mergeRequest):
        for repository in self.repositories:
            self.repositories[repository].checkout_fb_or_stable(mergeRequest).pull()
        return self

    def checkoutMaster(self):
        for repository in self.repositories:
            self.repositories[repository].checkoutMaster()
        return self

    def clean(self):
        for repository in self.repositories:
            self.repositories[repository].clean()
        return self

    def getHeads(self):
        hashes = dict()
        hashes["bss"] = self.repositories["bss"].getHead()
        hashes["tum"] = self.repositories["tum"].getHead()
        return hashes

    def logCommitsBetweenFBAndStable(self, mergeRequest):
        return [commit for repository in self.repositories for commit in self.repositories[repository].logCommitsBetweenFBAndStable(mergeRequest)]

    def logJiraIssuesBetweenFBAndStable(self, mergeRequest):
        commits = self.logCommitsBetweenFBAndStable(mergeRequest)
        jiraIssues = [jiraIssue for jiraIssue in [jira.getJiraIdFromCommitMsg(commit[1]) for commit in commits] if jiraIssue]
        return np.unique(jiraIssues)

    def cloneBranch(self, targetBranch, sourceBranch):
        for repository in self.repositories:
            self.repositories[repository].cloneBranch(targetBranch, sourceBranch)
        return self

    def get_available_solutions(self):
        solutions_path = Path() / self.repositories["bss"].path / 'solutions'
        # return [file.name for file in solutions_path.iterdir() if file.is_dir()]
        solutions = [file.name for file in solutions_path.iterdir() if file.is_dir()]
        return list(filter(lambda solution: solution in ['ngena', 'olu', 'ibu'], solutions))
dodaje main
