import requests
import flask
import matplotlib
import json

matplotlib.use('Agg')

import schemdraw
import schemdraw.elements as elm
from schemdraw import flow

import json

entreelist={}
mergelist={}
thinglist={}

ENTREE_NS=1000
MERGE_NS=1002


app = flask.Flask(__name__)

def getLabel(entry):
    return entry.name

def findId(title, entries):
    for key in entries:
        entry = entries[key]
        if entry.name.split(':')[1] == title:
            return key
    return None

class organizer:

    # how do we make our organizer also get diagrams from other organizers?
    # sometimes, trees aren't paired with a merge

    def __init__(self, root):
        self.protodiagram=[]
        self.diagram=schemdraw.Drawing()
        self.root=root
        # for temp in range(len(self.root.path)):
        #     self.protodiagram.append([])
        #     self.protodiagram[temp].append(self.root.path[temp])

        self.protodiagram.append([])
        self.protodiagram[-1].append(self.root)
        # self.rootentree.depth=0 this one should be determined by getdiagram() function. not here. consistency!

    def addfuture(self, toadd):
        print("adding " + toadd.root.name + "'s future to " + self.root.name + "'s future")
        while len(self.protodiagram) < len(toadd.root.path) + len(toadd.protodiagram):
            self.protodiagram.append([])

        try:

            offset=len(toadd.root.path) - toadd.root.path.index(self.root)

            for temp in range(len(toadd.protodiagram)):
                for item in toadd.protodiagram[temp]:
                    print("adding " + item.name + " to depth " + str(temp+offset) + " in future of " + self.root.name)
                    self.protodiagram[temp+offset].append(item)

        except ValueError:
            print("screw off")
        print("************")


    def processmerges():
        # moves from very last elements to the front. deletes repeats when they encounter them. probably gonna use a hashmap/dictionary to process the list
        print("removing extra merges")


    def drawandsave(self, imgname):
        print("drawing and saving")

        offset=len(self.root.path)

        for temp in range(offset):
            self.diagram += self.root.path[temp].block.at((temp*5, 0))

        for temp in range(len(self.protodiagram)):
            for itemtemp in range(len(self.protodiagram[temp])):
                self.diagram += self.protodiagram[temp][itemtemp].block.at(((offset+temp)*5, -itemtemp*5))

        self.root.path.append(self.root)
        for temp in range(offset):
            self.diagram += elm.Wire('-', arrow='->').hold().at(self.root.path[temp].block.E).to(self.root.path[temp+1].block.W)
            #self.diagram += elm.Wire('-', arrow='->').hold().at(self.root.path[-1].block.E).to(self.root.block.W)

        for temp in range(len(self.protodiagram)):
            for itemtemp in range(len(self.protodiagram[temp])):
                for itemitemtemp in self.protodiagram[temp][itemtemp].children:
                    if istroublemaker(self.root, itemitemtemp):
                        print("no")
                    else:
                        print("drawing wire from " + self.protodiagram[temp][itemtemp].name + " to " + itemitemtemp.name)
                        print(itemitemtemp.block.W)
                        self.diagram += elm.Wire('-', arrow='->').hold().at(self.protodiagram[temp][itemtemp].block.E).to(itemitemtemp.block.W)

        self.diagram.draw()
        self.diagram.save(imgname + ".svg")

        with open(imgname + '.json', 'w') as file: file.write(json.dumps(self.root.saveable))

        # place the blocks in the right directions, then draw wires from each block to its children (or to its parents, that might be easier)


class entree:

    def __init__(self, ident, authorname, name, date, entreetype, parent, performance):
#                      ("B", "hyang", "B", "1", "entry", "hyang-2-1", None),

        self.ident=ident

        self.authorname=authorname
        self.name=name
        self.date=date
        self.block=flow.Box(w=3, h=1.5).label(getLabel(self)).hold()

        self.entreetype=entreetype

        self.pairedmerge=None

        self.parents=list()
        if parent:
            self.parent.append(parent)
        self.children=[]
        self.troublemakers=[]
        self.performance=performance

        self.path=None
        self.future=None
        self.depth=None

        self.saveable=[]


    def setpath(self):
        if len(self.parents) > 0:
            print(self.name + ": ", end="")
            parent = self.parents[0]
            print(parent)
            print(thinglist.keys())
            if thinglist[parent].path:
                self.path=thinglist[self.parents[0]].path + [thinglist[self.parents[0]]]
            else:
                self.path=[thinglist[self.parents[0]]]
            for perpath in self.path:
                print(perpath.name + ", ", end="")
            #print("setpath: " + str(self.path))
            print("\n")
        else:
            self.path=[]


    def makefuture(self):

        self.future=organizer(self)

        stack=[]
        stack.extend(reversed(self.children))

        while len(stack) > 0:

            print("entry running makefuture(): " + self.name)
            print("entreestack view (bottom to top): " , end="")
            for perentree in stack:
                print(perentree.name+" ", end="")
            print("\n***")

            temp=stack.pop(-1)
            self.saveable.append(temp.ident)


            if istroublemaker(self, temp):
                    self.troublemakers.append(temp)
            else:
                # we will run the setpath() here, for the temp element. only here.
                temp.setpath()
                stack.extend(reversed(temp.makefuture()))
                self.future.addfuture(temp.future)

        return self.troublemakers


class merge:

    def __init__(self, ident, authorname, name, date, pairedentree, performance):

        self.ident=ident

        self.authorname=authorname
        self.name=name
        self.date=date
        self.block=flow.Box(w=3, h=1.5).label(getLabel(self)).hold()

        self.pairedentree=pairedentree

        self.pairedmerge=self

        self.parents=[]
        self.children=[]
        self.troublemakers=[]
        self.performance=performance

        self.path=None
        self.entreeorganizer=None
        self.depth=None

        self.done=False


        self.saveable=[]

    def setpath(self):
        for perparent in self.parents:
            if perparent.path is not None:
                if self.path is not None:
                    if len(self.path) < len(perparent.path + [perparent]):
                        self.path=perparent.path + [perparent]
                else:
                    self.path=perparent.path + [perparent]

        print(self.name + ": ", end="")
        for perpath in self.path:
            print(perpath.name + ", ", end="")
        #print("setpath: " + str(self.path))
        print("\n")

    def makefuture(self):

        global entreelist
        global mergelist



        if self.done == False:

            self.future=organizer(self)

            stack=[]
            stack.extend(reversed(self.children))

            while len(stack) > 0:

                print("entry running makefuture(): " + self.name)
                print("entreestack view (bottom to top): " , end="")
                for perentree in stack:
                    print(perentree.name+" ", end="")
                print("\n***")

                temp=stack.pop(-1)
                self.saveable.append(temp.ident)


                if istroublemaker(self, temp):
                    self.troublemakers.append(temp)
                else:
                    temp.setpath()
                    stack.extend(reversed(temp.makefuture()))
                    self.future.addfuture(temp.future, temp.path)

            self.done=True
            return self.troublemakers
        else:
            return []


def istroublemaker(caller, subject):

    if caller.pairedmerge != None:
        if subject in caller.pairedmerge.children:
            print(subject.name + " is a troublemaker")
            return True
        else:
            if entreelist[caller.pairedmerge.pairedentree] is caller:
                return False
            else:
                if len(caller.children) < len(subject.children):
                    print(subject.name + " is a troublemaker")
                    return True
                else:
                    return False
    else:
        if len(caller.children) < len(subject.children):
            print(subject.name + " is a troublemaker")
            return True
        else:
            return False

def getentries():
    global entreelist
    global mergelist
    global thinglist

    USERNAME = "Magmawolf8@Recordsdiagram"
    PASSWORD = "7tmsdolu8hdgfm24f463eng5vh9fag6o"

    S = requests.Session()

#    api_url = 'http://records:8080/api.php'
    api_url = 'http://mediawiki:80/api.php'


    # get a token for logging in,

    PARAMS_0 = {
        'action':"query",
        'meta':"tokens",
        'type':"login",
        'format':"json"
    }

    print(f"Get from {api_url}")
    R = S.get(url=api_url, params=PARAMS_0)
    DATA = R.json()

    LOGIN_TOKEN = DATA['query']['tokens']['logintoken']

    print(LOGIN_TOKEN)

    # Send a post request to login. 

    PARAMS_1 = {
        'action': "login",
        'lgname': USERNAME,
        'lgpassword': PASSWORD,
        'lgtoken': LOGIN_TOKEN,
        'format': "json"
    }

    print(f"Post to {api_url}")
    R = S.post(api_url, data=PARAMS_1)
    DATA = R.json()

    print(DATA)
    assert DATA['login']['result'] == 'Success'



    params_entree = {
        'action':"query",
        'list':"allpages",
        'apnamespace':ENTREE_NS,
        'format':"json"
    }

    params_merge = {
        'action':"query",
        'list':"allpages",
        'apnamespace':MERGE_NS,
        'format':"json"
    }

    entreelist = dict()
    mergelist = dict()
    response = S.get(api_url, params=params_entree)
    data_entree = response.json()

    print(f"Entree data: {data_entree}")

    for page in data_entree['query']['allpages']:
        page_id = str(page['pageid'])
#        page_creator = page['creator']
        page_title = page['title']
#        page_date = page['touched']
        page_namespace = page['ns']

        page_creator = "hyang"
        page_date = "1"

        if page_namespace == ENTREE_NS:
            instance = entree(str(page_id), page_creator, page_title, page_date, "entry", None, None)
            entreelist[page_id] = instance
            thinglist[page_id] = instance

        elif page_namespace == MERGE_NS:
            instance = merge(str(page_id), page_creator, page_title, page_date, None, None)
            mergelist[page_id] = instance
            thinglist[page_id] = instance

    response = S.get(api_url, params=params_merge)
    data_merge = response.json()

    print(f"Merge data: {data_merge}")

    for page in data_merge['query']['allpages']:
        page_id = str(page['pageid'])
#        page_creator = page['creator']
        page_title = page['title']
#        page_date = page['touched']
        page_namespace = page['ns']

        page_creator = "hyang"
        page_date = "1"

        if page_namespace == ENTREE_NS:
            instance = entree(str(page_id), page_creator, page_title, page_date, "entry", None, None)
            entreelist[page_id] = instance
            thinglist[page_id] = instance

        elif page_namespace == MERGE_NS:
            instance = merge(str(page_id), page_creator, page_title, page_date, None, None)
            mergelist[page_id] = instance
            thinglist[page_id] = instance




    for page in data_entree['query']['allpages']:
        page_id = str(page['pageid'])
        page_namespace = page['ns']

        params = {
            'action': 'query',
            'format': 'json',
            'titles': page['title'],
            'prop': 'categories'
        }
        response = S.get(api_url, params=params)
        pageInfo = response.json()
#        print(pageInfo)

        if 'categories' not in pageInfo['query']['pages'][page_id]:
            continue

        categories = pageInfo['query']['pages'][page_id]['categories']
#        print(categories)

        if page_namespace == ENTREE_NS:
            for category in categories:
                categoryName = category['title'].split(':')[1]
                print(categoryName)
                parent_id = findId(categoryName, thinglist)
                if parent_id:
                    print("parent ID found")
                    entreelist[page_id].parents.append(parent_id)
            print(f"{page_id}: {entreelist[page_id].parents}")
        elif page_namespace == MERGE_NS:
            for category in categories:
                categoryName = category['title'].split(':')[1]
                print(categoryName)
                parent_id = findId(categoryName, thinglist)
                if parent_id:
                    mergelist[page_id].pairedentree = parent_id
                    break

    for page in data_merge['query']['allpages']:
        page_id = str(page['pageid'])
        page_namespace = page['ns']

        params = {
            'action': 'query',
            'format': 'json',
            'titles': page['title'],
            'prop': 'categories'
        }
        response = S.get(api_url, params=params)
        pageInfo = response.json()
#        print(pageInfo)

        if 'categories' not in pageInfo['query']['pages'][page_id]:
            continue

        categories = pageInfo['query']['pages'][page_id]['categories']
#        print(categories)

        if page_namespace == ENTREE_NS:
            for category in categories:
                categoryName = category['title'].split(':')[1]
                print(categoryName)
                parent_id = findId(categoryName, thinglist)
                if parent_id:
                    entreelist[page_id].parents.append(parent_id)
            print(f"{page_id}: {entreelist[page_id].parents}")
        elif page_namespace == MERGE_NS:
            for category in categories:
                categoryName = category['title'].split(':')[1]
                print(categoryName)
                for thingkey in thinglist:
                    print(thinglist[thingkey].name)
                parent_id = findId(categoryName, thinglist)
                if parent_id:
                    mergelist[page_id].pairedentree = parent_id
                    break



    return 0

def getfromcsv():

    print("getting entries from csv")
    # get both entrees and merges

def main():

    global entreelist
    global mergelist

    entreelist = dict()
    mergelist = dict()
    '''
    entreelist={"hyang-1-1":entree("1", "hyang", "1", "1", "entry", None, None),
                "hyang-2-1":entree("2", "hyang", "2", "1", "entry", "hyang-1-1", None),
                "hyang-A-1":entree("A", "hyang", "A", "1", "entry", "hyang-2-1", None),
                "hyang-B-1":entree("B", "hyang", "B", "1", "entry", "hyang-2-1", None),
                "hyang-5-1":entree("5", "hyang", "5", "1", "entry", "hyang-I-1", None),
                "hyang-X-1":entree("X", "hyang", "X", "1", "entry", "hyang-I-1", None),
                "hyang-6-1":entree("6", "hyang", "6", "1", "entry", "hyang-5-1", None),
                "hyang-Y-1":entree("Y", "hyang", "Y", "1", "entry", "hyang-X-1", None),
                "hyang-3-1":entree("3", "hyang", "3", "1", "entry", "hyang-1-1", None),
                "hyang-4-1":entree("4", "hyang", "4", "1", "entry", "hyang-3-1", None),
                "hyang-C-1":entree("C", "hyang", "C", "1", "entry", "hyang-4-1", None),
                "hyang-E-1":entree("E", "hyang", "E", "1", "entry", "hyang-C-1", None),
        		"hyang-7-1":entree("7", "hyang", "7", "1", "entry", "hyang-E-1", None),
                "hyang-D-1":entree("D", "hyang", "D", "1", "entry", "hyang-4-1", None)}

    mergelist={
        "hyang-I-1":merge("I", "hyang", "I", "1", "hyang-2-1", None),
        "hyang-II-1":merge("II", "hyang", "II", "1", "hyang-4-1", None),
        "hyang-III-1":merge("III", "hyang", "III", "1", "hyang-1-1", None)
    }
    '''

    getentries()

    # sort merges by submission date too
    # add a provision in the entree children sorting to add children to merges also
    # add a provision in the merge children sorting so merges can count as leaf nodes. cuz they might be.

    for entreekey in entreelist:
        # entreelist should be in order of submission, so we don't have to check if the parent's been graphed. we're not even graphing here!
        # use of the ID of the entrees stops here. we convert the parents tab to children tab, and make sure that the children are entree objects, not the keys to them.
        entry = entreelist[entreekey]
        if len(entry.parents) == 0:
            continue
        for parent_id in entry.parents:
            if parent_id in entreelist:
                entreelist[parent_id].children.append(entreelist[entreekey])

            if parent_id in mergelist:
                mergelist[parent_id].children.append(entreelist[entreekey])



    entreestack=[]

    for mergekey in mergelist:
        # find leaf nodes of the paired entree, then add merge as a child of all of these. then, we're finished.
        # we still need a pairedmerge in every entree object, because if we're merging some tree that contains merges already, we need to skip across the entire tree so our stack doesn't crap itself
        # when it comes time to assign a height to the merge, don't do it as a parameter to the addentreeormerge() function. have the organizer object take care of that by itself, inside the function drawandsave()

        entreestack.append(entreelist[mergelist[mergekey].pairedentree])

        while len(entreestack) > 0:

            tempentree=entreestack.pop(-1)

            if len(tempentree.children) > 0: # we're assuming it's not a merge, hoping the data is clean. we're also assuming there aren't duplicate merges. we're assuming a lot of things. we're also assuming that you won't have make(big)make(small)merge(big)merge(small) because that's dumb, but if there was, it would cause problems.
                if type(tempentree) is entree:

                    # if tempentree.name=="4":
                    #     print("4 has a pairedmerge?"+str(tempentree.pairedmerge!=None)+" the current merge is "+mergelist[mergekey].name)
                    # if tempentree.name=="C":
                    #     print("we're going in")
                    if tempentree.pairedmerge==None:
                        for perchild in tempentree.children:
                            entreestack.append(perchild)
                        tempentree.pairedmerge=mergelist[mergekey]
                    else:
                        # skip directly to the paired merge
                        entreestack.append(tempentree.pairedmerge)
                elif type(tempentree) is merge:
                    for perchild in tempentree.children:
                        entreestack.append(perchild)
                else: # something's wrong
                    print("I just got an entree that wasn't class entree or merge. Something's probably wrong\n")
            else: # tempentree is a leaf node of the tree that's paired with this merge
                # add the current merge to the children of the tempentree
                if type(tempentree) is not merge: # merges are always their own pairs
                    tempentree.pairedmerge=mergelist[mergekey]
                tempentree.children.append(mergelist[mergekey])
                mergelist[mergekey].parents.append(tempentree)

    for perentree in entreelist:
        thinglist[perentree]=entreelist[perentree]

    for permerge in mergelist:
        thinglist[permerge]=mergelist[permerge]

    for perentree in entreelist:
        entreelist[perentree].setpath()
        entreelist[perentree].makefuture()
#    entreelist[next(iter(entreelist))].setpath()
#    entreelist[next(iter(entreelist))].makefuture()

    # for temp in entreelist["hyang-2-1"].future.protodiagram:
    #     for thing in temp:
    #         print(thing.name, end=", ")
    #     print("")
    # print("")

    for perentree in entreelist:
        print(f"Draw {perentree}")
        try:
            print(entreelist[entreelist[perentree].parents[0]].ident)
        except Exception as e:
            print(str(entreelist[perentree].ident) + " is an original gangster " + str(e))

        if entreelist[perentree].ident == "43":
            print(entreelist[entreelist[perentree].parents[0]].ident)

        if entreelist[perentree].future:
            print("Draw")
            entreelist[perentree].future.drawandsave(str(perentree))

    for permerge in mergelist:
        if mergelist[permerge].future:
            mergelist[permerge].future.drawandsave(str(permerge))

    return "a-OK!"

    #entreelist["hyang-2-1"].future.drawandsave()
    #print(mergelist["hyang-III-1"].path)

    # for item in entreelist[next(iter(entreelist))].entreeorganizer.protodiagram:
    #     print(item.name + " has depth " + str(entreelist[next(iter(entreelist))].entreeorganizer.protodiagram[item]) + ", ", end="")

    #print(str(entreelist[next(iter(entreelist))].entreeorganizer.protodiagram))






@app.route("/serve-image/<image_id>")
def serve_image(image_id):
    file_name = f"{image_id}.svg"  # Assuming the file extension is ".svg"
    print(file_name)
    return flask.send_file(file_name, mimetype='image/svg+xml')

@app.route("/serve-childlist/<child_id>")
def serve_childlist(child_id):
    with open(f'{child_id}.json') as json_file:
        childlist_data = json.load(json_file)
    return childlist_data

@app.route("/run")
def run():
    main()
    return "complete"

@app.route("/")
def root():
  return "<h1> Root </h1>"  


if __name__ == "__main__":
    print("Start")
    app.run(host="0.0.0.0")
