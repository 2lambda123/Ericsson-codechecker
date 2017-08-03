// -------------------------------------------------------------------------
//                     The CodeChecker Infrastructure
//   This file is distributed under the University of Illinois Open Source
//   License. See LICENSE.TXT for details.
// -------------------------------------------------------------------------

define([
  'dojo/_base/declare',
  'dojo/topic',
  'dojo/dom-construct',
  'dijit/Dialog',
  'dijit/DropDownMenu',
  'dijit/MenuItem',
  'dijit/form/DropDownButton',
  'dijit/layout/BorderContainer',
  'dijit/layout/ContentPane',
  'dijit/layout/TabContainer',
  'codechecker/hashHelper',
  'codechecker/ListOfBugs',
  'codechecker/ListOfRuns',
  'codechecker/util'],
function (declare, topic, domConstruct, Dialog, DropDownMenu, MenuItem,
  DropDownButton, BorderContainer, ContentPane, TabContainer, hashHelper,
  ListOfBugs, ListOfRuns, util, filterHelper) {

  return function () {

    //---------------------------- Global objects ----------------------------//

    CC_SERVICE = new codeCheckerDBAccess.codeCheckerDBAccessClient(
      new Thrift.Protocol(new Thrift.Transport("CodeCheckerService")));
    CC_AUTH_SERVICE =
      new codeCheckerAuthentication.codeCheckerAuthenticationClient(
        new Thrift.TJSONProtocol(
          new Thrift.Transport("/Authentication")));

    CC_OBJECTS = codeCheckerDBAccess;

    //----------------------------- Main layout ------------------------------//

    var layout = new BorderContainer({ id : 'mainLayout' });

    var headerPane = new ContentPane({ id : 'headerPane', region : 'top' });
    layout.addChild(headerPane);

    var runsTab = new TabContainer({ region : 'center' });
    layout.addChild(runsTab);

    //--- Logo ---//

    var logoContainer = domConstruct.create('div', {
      id : 'logo-container'
    }, headerPane.domNode);

    var logo = domConstruct.create('span', { id : 'logo' }, logoContainer);

    var logoText = domConstruct.create('div', {
      id : 'logo-text',
      innerHTML : 'CodeChecker'
    }, logoContainer);

    var version = domConstruct.create('span', {
      id : 'logo-version',
      innerHTML : CC_SERVICE.getPackageVersion()
    }, logoText);

    var user = CC_AUTH_SERVICE.getLoggedInUser();
    var loginUserSpan = null;
    if (user.length > 0) {
      loginUserSpan = domConstruct.create('span', {
        id: 'loggedin',
        innerHTML: "Logged in as " + user + "."
      });
    }

      //--- Menu button ---//

    var credits = new Dialog({
      title : 'Credits',
      class : 'credits',
      content :
        '<b>D&aacute;niel Krupp</b> <a href="https://github.com/dkrupp">@dkrupp</a><br>daniel.krupp@ericsson.com<br> \
         <b>Gy&ouml;rgy Orb&aacute;n</b> <a href="https://github.com/gyorb">@gyorb</a><br>gyorgy.orban@ericsson.com<br> \
         <b>Boldizs&aacute;r T&oacute;th</b> <a href="https://github.com/bobszi">@bobszi</a><br>toth.boldizsar@gmail.com<br> \
         <b>G&aacute;bor Alex Isp&aacute;novics</b> <a href="https://github.com/igalex">@igalex</a><br>gabor.alex.ispanovics@ericsson.com<br> \
         <b>Bence Babati</b> <a href="https://github.com/babati">@babati</a><br>bence.babati@ericsson.com<br> \
         <b>G&aacute;bor Horv&aacuteth</b> <a href="https://github.com/Xazax-hun">@Xazax-hun</a><br>gabor.a.horvath@ericsson.com<br> \
         <b>Szabolcs Sipos</b> <a href="https://github.com/labuwx">@labuwx</a><br>labuwx@balfug.com<br> \
         <b>Tibor Brunner</b> <a href="https://github.com/bruntib">@bruntib</a><br>tibor.brunner@ericsson.com<br>'
    });

    var menuItems = new DropDownMenu();

    menuItems.addChild(new MenuItem({
      label : 'Link to GitHub',
      onClick : function () {
        window.open('https://github.com/Ericsson/codechecker', '_blank');
      }
    }));

    menuItems.addChild(new MenuItem({
      label : 'Report a bug here',
      onClick : function () {
        window.open('https://github.com/Ericsson/codechecker/issues/new', '_blank');
      }
    }));

    menuItems.addChild(new MenuItem({
      label : 'Credits',
      onClick : function () { credits.show(); }
    }));

    var menuButton = new DropDownButton({
      class : 'mainMenuButton',
      iconClass : 'dijitIconFunction',
      dropDown : menuItems
    });

    var headerMenu = domConstruct.create('div', {
        id : 'header-menu'
      });

    if (loginUserSpan != null)
        domConstruct.place(loginUserSpan, headerMenu);

    domConstruct.place(menuButton.domNode, headerMenu);


    domConstruct.place(headerMenu, headerPane.domNode);

    //--- Center panel ---//

    var listOfRuns = new ListOfRuns({
      title : 'List of runs',
      onLoaded : function (runDataList) {
        function findRunData(runId) {
          return util.findInArray(runDataList, function (runData) {
            return runData.runId === runId;
          });
        }

        var urlValues = hashHelper.getValues();
        if (urlValues.run) {
          topic.publish('openRun',
            findRunData(parseInt(urlValues.run)), urlValues.filters);
        } else if (urlValues.baseline && urlValues.newcheck){
          topic.publish('openDiff', {
            baseline : findRunData(parseInt(urlValues.baseline)),
            newcheck : findRunData(parseInt(urlValues.newcheck)),
            }, urlValues.filters
          );
        }

        if (urlValues.report)
          topic.publish('openFile', parseInt(urlValues.report));
      }
    });

    runsTab.addChild(listOfRuns);

    //--- Init page ---//

    document.body.appendChild(layout.domNode);
    layout.startup();

    //------------------------------- Control --------------------------------//

    var runIdToTab = {};

    topic.subscribe('openRun', function (runData, filters) {
      if (!(runData.runId in runIdToTab)) {
        runIdToTab[runData.runId] = new ListOfBugs({
          runData : runData,
          title : runData.name,
          filters : filters,
          closable : true,
          onClose : function () {
            delete runIdToTab[runData.runId];
            return true;
          },
          onShow : function () {
            hashHelper.setRun(runData.runId);
          }
        });

        runsTab.addChild(runIdToTab[runData.runId]);
      }

      runsTab.selectChild(runIdToTab[runData.runId]);
    });

    topic.subscribe('openDiff', function (diff, filters) {
      var tabId = diff.baseline.runId + ':' + diff.newcheck.runId;

      if (!(tabId in runIdToTab)) {
        runIdToTab[tabId] = new ListOfBugs({
          baseline : diff.baseline,
          newcheck : diff.newcheck,
          filters : filters,
          title : 'Diff of ' + diff.baseline.name + ' and ' + diff.newcheck.name,
          closable : true,
          onClose : function () {
            delete runIdToTab[tabId];
            return true;
          },
          onShow : function () {
            hashHelper.setDiff(diff.baseline.runId, diff.newcheck.runId);
          }
        });

        runsTab.addChild(runIdToTab[tabId]);
      }

      runsTab.selectChild(runIdToTab[tabId]);
    });

    var docDialog = new Dialog();

    topic.subscribe('showDocumentation', function (checkerId) {
      CC_SERVICE.getCheckerDoc(checkerId, function (documentation) {
        docDialog.set('title', 'Documentation for <b>' + checkerId + '</b>');
        docDialog.set('content', marked(documentation));
        docDialog.show();
      });
    });
  };
});
