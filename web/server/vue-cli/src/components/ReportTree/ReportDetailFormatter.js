import { ExtendedReportDataType } from "@cc/report-server-types";

import ReportTreeKind from "./ReportTreeKind";
import ReportStepIconType from "./ReportStepIconType";

const highlightColours = [
  "#ffffff",
  "#e9dddd",
  "#dde0eb",
  "#e5e8e5",
  "#cbc2b6",
  "#b8ccea",
  "#c1c9cd",
  "#a7a28f"
];

function getHighlightData(stack, step) {
  let msg = step.msg;

  // The background must be saved BEFORE stack transition.
  // Calling is in the caller, return is in the called func, not "outside"
  const highlight = {
    bgColor: stack.bgColor,
    icon: ReportStepIconType.DEFAULT
  };

  function extractFuncName(prefix) {
    if (msg.startsWith(prefix)) {
      msg = msg.replace(prefix, "").replace(/'/g, "");
      return true;
    }
  }

  if (extractFuncName("Calling ")) {
    stack.funcStack.push(msg);
    stack.bgColor = highlightColours[
      stack.funcStack.length % highlightColours.length];

    highlight.icon = ReportStepIconType.CALLING;
  } else if (msg.startsWith("Entered call from ")) {
    highlight.icon = ReportStepIconType.ENTERED_CALL;
  } else if (extractFuncName("Returning from ")) {
    if (msg === stack.funcStack[stack.funcStack.length - 1]) {
      stack.funcStack.pop();
      stack.bgColor = highlightColours[
        stack.funcStack.length % highlightColours.length];

      highlight.icon = ReportStepIconType.RETURNING;
    } else {
      console.warn("StackError: Returned from " + msg
        + " while the last function " + "was "
        + stack.funcStack[stack.funcStack.length - 1]);
    }
  } else if (msg === "Returned allocated memory") {
    stack.funcStack.pop();
    stack.bgColor = highlightColours[
      stack.funcStack.length % highlightColours];
    highlight.icon = ReportStepIconType.RETURNING;
  } else if (msg.startsWith("Assuming the condition")) {
    highlight.icon = ReportStepIconType.ASSUMING_CONDITION;
  } else if (msg.startsWith("Assuming")) {
    highlight.icon = ReportStepIconType.ASSUMING;
  } else if (msg == "Entering loop body") {
    highlight.icon = ReportStepIconType.ENTERING_LOOP_BODY;
  } else if (msg.startsWith("Loop body executed")) {
    highlight.icon = ReportStepIconType.LOOP_BODY_EXECUTED;
  } else if (msg == "Looping back to the head of the loop") {
    highlight.icon = ReportStepIconType.LOOP_BACK;
  }

  return highlight;
}

function formatExtendedData(report, extendedData) {
  const items = [];

  // Add macro expansions.
  const macros = extendedData.filter((data) => {
    return data.type === ExtendedReportDataType.MACRO;
  });

  if (macros.length) {
    const id = `${report.reportId}_${ReportTreeKind.MACRO_EXPANSION}`;
    const children = formatExtendedReportDataChildren(macros,
      ReportTreeKind.MACRO_EXPANSION_ITEM, id)

    items.push({
      id: id,
      name: "Macro expansions",
      kind: ReportTreeKind.MACRO_EXPANSION,
      children: children
    })
  }

  // Add notes.
  const notes = extendedData.filter((data) => {
    return data.type === ExtendedReportDataType.NOTE;
  });

  if (notes.length) {
    const id = `${report.reportId}_${ReportTreeKind.NOTE}`;
    const children = formatExtendedReportDataChildren(notes,
      ReportTreeKind.NOTE_ITEM, id)

    items.push({
      id: id,
      name: "Notes",
      kind: ReportTreeKind.NOTE,
      children: children
    })
  }

  return items;
}

function formatExtendedReportDataChildren(extendedData, kind, parentId) {
  return extendedData.sort((a, b) => {
    return a.startLine - b.startLine;
  }).map((data, index) => {
    return {
      id: `${parentId}_${index}`,
      name: data.message,
      kind: kind,
      data: data
    };
  });
}

function getReportStepIcon(step, index, isResult) {
  var type = isResult
    ? "error" : step.msg.indexOf(" (fixit)") > -1
    ? "fixit" : "info";

  return {
    index: index + 1,
    type: type
  };
}

function formatReportEvents(report, events) {
  const items = [];

  const highlightStack = {
    funcStack: [],
    bgColor: highlightColours[0]
  };

  // Indent path events on function calls.
  let indentation = 0;

  events.forEach(function (step, index) {
    const isResult = index === events.length - 1;

    const highlightData = getHighlightData(highlightStack, step);
    const reportStepIcon = getReportStepIcon(step, index, isResult);

    if (highlightData.icon === ReportStepIconType.ENTERED_CALL) {
      indentation += 1;
    } else if (highlightData.icon === ReportStepIconType.RETURNING) {
      indentation -= 1;
    }

    items.push({
      id : `${report.reportId}_${ReportTreeKind.REPORT_STEPS}_${index}`,
      name: report.checkerMsg,
      kind: ReportTreeKind.REPORT_STEPS,
      step: step,
      report: report,
      icon: highlightData.icon,
      reportStepIcon: reportStepIcon,
      bgColor: highlightData.bgColor,
      level: indentation
    });
  });

  return items;
}

export default function formatReportDetails(report, reportDetails) {
  const items = [];

  // Add extended items such as notes and macros.
  const extendedItems = formatExtendedData(report, reportDetails.extendedData);
  items.push(...extendedItems);

  // Add main report node.
  items.push({
    id : `${report.reportId}_${ReportTreeKind.BUG}`,
    name: report.checkerMsg,
    kind: ReportTreeKind.BUG,
    report: report
  });

  const reportSteps = formatReportEvents(report, reportDetails.pathEvents);
  items.push(...reportSteps);

  return items;
}