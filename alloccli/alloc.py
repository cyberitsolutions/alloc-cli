#!/usr/bin/env python

import os
import sys
import exceptions
import simplejson
import getopt
import re
import urllib
import datetime
from netrc import netrc
from urlparse import urlparse
from prettytable import PrettyTable

class alloc(object):

  url = ''
  username = ''
  quiet = ''
  sessID = ''
  field_names = {"taskID":"Task ID"
                ,"taskTypeID":"Type"
                ,"taskStatusLabel":"Status"
                ,"priority":"Task Pri"
                ,"projectPriority":"Proj Pri"
                ,"priorityFactor":"Pri Factor"
                ,"priorityLabel": "Priority"
                ,"timeExpected":"Est"
                ,"timeLimit":"Limit"
                ,"timeActual":"Act"
                ,"rate":"Rate"
                ,"projectName":"Project"
                ,"taskName":"Task"
                ,"taskDescription": "Description"
                ,"creator_name": "Creator"
                ,"manager_name": "Manager"
                ,"assignee_name": "Assigned"
                }

                #Other task fields, that may one day require labels
                #personID
                #closerID
                #creatorID
                #managerID
                #projectID
                #parentTaskID
                #duplicateTaskID
                #clientID
                #taskStatusColour
                #rateUnit
                #rateUnitID
                #currency
                #taskComments
                #percentComplete
                #timeWorst
                #taskTypeImage
                #dateTargetCompletion
                #projectShortName
                #taskStatus
                #dateAssigned
                #project_name
                #dateClosed
                #dateCreated    
                #dateTargetStart
                #newSubTask
                #taskLink                                          
                #taskURL                                 
                #dateActualStart
                #taskModifiedUser
                #dateActualCompletion
                #timeBest




  row_timeSheet = ["timeSheetID","ID","dateFrom","From","dateTo","To","status","Status","person","Owner","duration","Duration","totalHours","Hrs","amount","$","projectName","Project"]
  row_timeSheetItem = ["timeSheetID","ID","timeSheetItemID","Item ID","dateTimeSheetItem","Date","taskID","taskID","comment","Comment","timeSheetItemDuration","Hours","rate","$","worth","Worth","hoursBilled","Total","taskLimit","Limit","limitWarning","Warning"]

  def __init__(self,url=""):
    if not url:
      dir = sys.path[0].split("/")[-2]
      if dir == "alloc":       url = "http://alloc/services/json.php"
      if dir == "alloc_stage": url = "http://alloc_stage/services/json.php"
      if dir == "alloc_dev":   url = "http://soy/alloc_dev/services/json.php"

    self.url = url
    self.username = ''
    self.quiet = ''
    self.csv = False
    self.sessID = ''

  def search_for_project(self, projectName, personID=None):
    # Search for a project like *projectName*
    if projectName:
      filter = {}
      if personID: filter["personID"] = personID
      filter["projectStatus"] = "Current"
      filter["projectName"] = projectName
      projects = self.get_list("project",filter)
      if len(projects) == 0:
        self.die("No project found matching: %s" % projectName)
      elif len(projects) > 1:
        self.print_table(projects, ["projectID","ID","projectName","Project"])
        self.die("Found more than one project matching: %s" % projectName)
      elif len(projects) == 1:
        return projects.keys()[0]
        
  def search_for_task(self, ops):
    # Search for a task like *taskName*
    if "taskName" in ops:
      tasks = self.get_list("task",ops)
      
      if not tasks:
        self.die("No task found matching: %s" % ops["taskName"])
      elif tasks and len(tasks) >1:
        self.print_table(tasks, ["taskID","ID","taskName","Task","projectName","Project"])
        self.die("Found more than one task matching: %s" % ops["taskName"])
      elif len(tasks) == 1:      
        return tasks.keys()[0]   

  def search_for_client(self, ops):
    # Search for a client like *clientName*
    if "clientName" in ops:
      clients = self.get_list("client",ops)

      if not clients:
        self.die("No client found matching: %s" % ops["clientName"])
      elif clients and len(clients) >1:
        self.print_table(clients, ["clientID","ID","clientName","Client"])
        self.die("Found more than one client matching: %s" % ops["clientName"])
      elif len(clients) == 1:
        return clients.keys()[0]

  def print_task(self, id):
    # print a descriptive view of a task
    rtn = self.get_list("task",{"taskID": id})

    # Print it out
    self.print_table(rtn, ["taskID","Task ID","projectID","Project","status","Status","person","Owner"])

  def get_args(self, ops, str):
    # This function allows us to handle the cli arguments elegantly
    short_ops = ""
    long_ops = []
    help_str = ""
    options = []
    all_ops = {}
    rtn = {}
    remainder = ""
    
    for x in ops:

      # These args go straight to getops
      short_ops += x[0]
      long_ops.append(re.sub("=.*$","=",x[1]).strip())

      # These are used to build up the help text for --help
      c = " " #spacing
      s = "    " #spacing
      l = "                   " #spacing
      if x[0] and x[1]: c = ","
      if x[0]: s = "  -"+x[0].replace(":","")
      if x[1].strip(): l = c+" --"+x[1]

      # eg:  -q, --quiet             Run with less output.
      help_str += s+l+"   "+x[2]+"\n"

      # And this is used below to build up a dictionary to return
      all_ops[re.sub("=.*$","",x[1]).strip()] = ["-"+x[0].replace(":",""), "--"+re.sub("=.*$","",x[1]).strip()]
    
    try:
      options, remainder = getopt.getopt(sys.argv[2:], short_ops, long_ops)
    except:
      print str % (os.path.basename(" ".join(sys.argv[0:2])), help_str.rstrip())
      sys.exit(0)

    for k,v in all_ops.items():
      rtn[k] = ""
      for opt, val in options:
        if opt in v:
          if val != "": # have to do it like this for eg -q which has no args
            rtn[k] = val
          else:
            rtn[k] = True

    if rtn['help']:
      print str % (os.path.basename(" ".join(sys.argv[0:2])), help_str.rstrip())
      sys.exit(0)
    
    return rtn, remainder

  def get_my_personID(self):
    # Get current user's personID
    ops = {}
    ops["username"] = self.username
    rtn = self.get_list("person",ops)
    for i in rtn:
      return i

  def get_only_these_fields(self,rows,only_these_fields):
    rtn = []
    inverted_field_names = dict([[v,k] for k,v in self.field_names.items()])

    # Allow the display of custom fields
    if type(only_these_fields) == type("string"):
      # Print all fields
      if only_these_fields.lower() == "all":
        for k,v in rows.items():
          for name,value in v.items():
            rtn.append(name)
            if name in self.field_names:
              rtn.append(self.field_names[name])
            else:
              rtn.append(name)
          break
      # Print a selection of fields
      else:
        f = only_these_fields.split(",")
        for name in f:
          if name in inverted_field_names:
            name = inverted_field_names[name]
          rtn.append(name)
          if name in self.field_names:
            rtn.append(self.field_names[name])
          else:
            rtn.append(name)
      return rtn;
    return only_these_fields

  def get_sorted_rows(self,rows,sortby,fields):
    rows = rows.items()
    if not sortby:
      return rows
    inverted_field_names = dict([[v,k] for k,v in self.field_names.items()])

    sortby = sortby.split(",")
    sortby.reverse()    

    def sort_func(row):
      try: val = row[1][inverted_field_names[f]]
      except:
        try: val = row[1][self.field_names[f]]
        except:
          try: val = row[1][f]
          except:
            try: val = row[1][fields[fields.index(f)-1]]
            except:
              return ''

      try: return int(val)
      except:
        try: return float(val)
        except:
          try: return val.lower()
          except:
            return val

    for f in sortby:
      if f:
        reverse = False
        if f[0] == "_":
          reverse = True
          f = f[1:]
        rows = sorted(rows, key=sort_func, reverse=reverse)
    return rows

  def print_table(self, rows, only_these_fields, sort=False, transforms={}):
    # For printing out results in an ascii table or CSV format
    if self.quiet: return

    table = PrettyTable()

    only_these_fields = self.get_only_these_fields(rows,only_these_fields)
    field_names = only_these_fields[1::2]
    table.set_field_names(field_names)

    # Re-order the table, this changes the dict to a list i.e. dict.items().
    rows = self.get_sorted_rows(rows,sort,only_these_fields)

    # Hide the frame and header if --csv
    if self.csv:
      table.set_border_chars(vertical=",",horizontal="",junction="")
      table.padding_width=0

    for label in field_names:
      if '$' in label:
        table.set_field_align(label, "r")
      else:
        table.set_field_align(label, "l")

    if rows:
      for k,row in rows:
        r = []
        for v in only_these_fields[::2]: 
          str = ''
      
          for sep in ["|"," ","/"]:
            if sep in v:
              bits = v.split(sep)
              str = sep.join([(row[i] or "") for i in bits])
              
          if v in row: str = row[v]
  
          if v in transforms:
            str = transforms[v](str)

          if not str: str = ''
          r.append(str)
        table.add_row(r)
    lines = table.get_string(header=not self.csv)
    # If csv, need to manually strip out the leading and trailing tab on
    # each line as well as compress the whitespace in the fields
    if self.csv:
      s = ''
      for line in lines[1:-1].split("\n"):
        line = re.sub("\s+,",",",line) # strip out whitespace padding 
        s+= line[1:-1]+"\n"            # strip out leading and trailing character
      lines = s[:-1]

    print lines

  def is_num(self, obj):
    # There's got to be a better way to tell if something is a number 
    # isinstance of float or int didn't do the job (for some reason ...)
    try:
      if obj is not None and float(obj) >= 0:
        return True;
    except:
      pass

    return False

  def get_credentials(self):
    # Obtain the user's alloc login credentials
    username = os.environ.get('ALLOC_USER')
    password = os.environ.get('ALLOC_PASS')
      
    if username is None or password is None:
      try:
        (username, _, password) = netrc().hosts[urlparse(self.url).hostname]
      except exceptions.IOError, e:
        pass
    
    if username is None or password is None:
      print "    The settings ALLOC_USER and ALLOC_PASS are required."
      print "    Set them either in the environment or in your ~/.netrc eg:"
      print "    machine alloc login $USER password $PASS"
      sys.exit(1)

    return username, password
    
  def add_time_by_task(self, taskID, duration, date, comments):
    # Add time to a time sheet using a task as reference
    if self.dryrun: return {'timeSheetID':''}
    args = {}
    args["taskID"] = taskID
    args["duration"] = duration
    args["date"] = date
    args["comments"] = comments
    args["method"] = "add_timeSheetItem_by_task"
    return self.make_request(args)

  def add_time_by_project(self, projectID, duration, date, comments):
    # Add time to a time sheet using a project as reference
    if self.dryrun: return {'timeSheetID':''}
    args = {}
    args["projectID"] = projectID
    args["duration"] = duration
    args["date"] = date
    args["comments"] = comments
    args["method"] = "add_timeSheetItem_by_project"
    return self.make_request(args)

  def get_list(self, entity, options):
    options["skipObject"] = '1'
    options["return"] = "array"
    args = {}
    args["entity"] = entity
    args["options"] = options
    args["method"] = "get_list"
    return self.make_request(args)

  def get_help(self, topic): 
    args = {}
    args["topic"] = topic
    args["method"] = "get_help"
    return self.make_request(args)

  def authenticate(self):
    username, password = self.get_credentials()
    # The user-agent must be identical between authenticated
    # requests, alloc uses the u-a for secondary auth
    allocUserAgent.version = 'alloc-cli %s' % username
    urllib._urlopener = allocUserAgent()
    args =  { "username": username, "password" : password }
    rtn = self.make_request(args)
    if "sessID" in rtn and rtn["sessID"]:
      self.sessID = rtn["sessID"]
      self.username = username
      return self.sessID
    else:
      self.die("Error authenticating: %s" % rtn)

  def make_request(self, args):
    args["sessID"] = self.sessID
    rtn = urllib.urlopen(self.url, urllib.urlencode(args)).read()
    try:
      return simplejson.loads(rtn)
    except:
      self.err("Error: %s" % rtn)
      self.die("Args: %s" % args)

  def get_alloc_html(self,url):
    return urllib.urlopen(url).read()

  def today(self):
    return datetime.date.today()

  def msg(self,str):
    if not self.quiet: print "---",str

  def yay(self,str):
    if not self.quiet: print ":-)",str

  def err(self,str):
    sys.stderr.write("!!! "+str+"\n")

  def die(self,str):
    self.err(str)
    sys.exit(1)

  def parse_email(self, email):
    addr = ''
    name = ''
    bits = email.split(' ')

    if len(bits) == 1:
      if '@' in bits[0]:
        addr = bits[0].replace('<','').replace('>','')
      else:
        name = bits[0]

    elif len(bits) > 1:

      if '@' in bits[-1:][0]:
        addr = bits[-1:][0].replace('<','').replace('>','')
        name = ' '.join(bits[:-1])
      else:
        name = ' '.join(bits)

    return addr, name

  def person_to_personID(self,name):

    if type(name) == type('string'):
      ops = {}
      if ' ' in name:
        ops['firstName'], ops['surname'] = name.split(" ")
      else:
        ops["username"] = name

      rtn = self.get_list("person",ops)
      if rtn:
        for i in rtn:
          return i

    # If they don't want all the records, then return an impossible personID
    if name != '%' and name != '*' and name.lower() != 'all':
      return '1000000000000000000' # returning just zero doesn't work
  

# Specify the user-agent 
class allocUserAgent(urllib.FancyURLopener):
  pass


