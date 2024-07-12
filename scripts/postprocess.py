import sys, os, json, csv, copy, math, re, itertools, html

from collections import Counter, OrderedDict
import benchmarks
from tools import *

OUT_DIR = "data"

def load_json(path : str):
    with open(path, 'r', encoding='utf-8-sig') as json_file:
        return json.load(json_file, object_pairs_hook=OrderedDict)

def save_json(json_data, path : str):
    with open(path, 'w') as json_file:
        json.dump(json_data, json_file, ensure_ascii=False, indent='\t')

def load_csv(path : str, delim='\t'):
    with open(path, 'r') as csv_file:
        return list(csv.reader(csv_file, delimiter=delim))

def save_csv(csv_data, path : str, delim='\t'):
    with open(path, 'w') as csv_file:
        writer = csv.writer(csv_file, delimiter=delim)
        writer.writerows(csv_data)
        
def save_html(table_data, num_tool_configs, path):
    SHOW_UNSUPPORTED = True # Also add entries for benchmarks that are known to be unsupported
    LOGS_SUBDIR = "logs"
    if not os.path.exists(os.path.join(path, LOGS_SUBDIR)): os.makedirs(os.path.join(path, LOGS_SUBDIR))
    
    # Aux function for writing in files with proper indention
    def write_line(file, indention, content):
        file.write("\t"*indention + content + "\n")
        
    # Generates an html log page for the given result within path/LOGS_SUBDIR/
    def create_log_page(result_json):
        with open(result_json["log"], 'r') as logfile:
            log = logfile.read()
        f_path = os.path.join(LOGS_SUBDIR, os.path.basename(result_json["log"])[:-4] + ".html")
        with open(os.path.join(path, f_path), 'w') as f:
            indention = 0
            write_line(f, indention, "<!DOCTYPE html>")
            write_line(f, indention, "<html>")
            write_line(f, indention, "<head>")
            indention += 1
            write_line(f, indention, '<meta charset="UTF-8">')
            write_line(f, indention, "<title>{}.{} - {}</title>".format(result_json["tool"], result_json["configuration-id"], result_json["benchmark-id"]))
            write_line(f, indention, '<link rel="stylesheet" type="text/css" href=../style.css>')
            indention -= 1
            write_line(f, indention, '</head>')
            write_line(f, indention, '<body>')
            write_line(f, indention, '<h1>{}.{}</h1>'.format(result_json["tool"],result_json["configuration-id"]))

            write_line(f, indention, '<div class="box">')
            indention += 1
            write_line(f, indention, '<div class="boxlabelo"><div class="boxlabelc">Benchmark</div></div>')
            write_line(f, indention, '<table style="margin-bottom: 0.75ex;">')
            indention += 1
            write_line(f, indention, '<tr><td>id:</td><td>{} ({})</td></tr>'.format(result_json["benchmark-id"], result_json["benchmark"]["model"]["type"].upper()))
            indention -= 1
            write_line(f, indention, "</table>")
            indention -= 1
            write_line(f, indention, "</div>")

            write_line(f, indention, '<div class="box">')
            indention += 1
            write_line(f, indention, '<div class="boxlabelo"><div class="boxlabelc">Invocation ({})</div></div>'.format(result_json["configuration-id"]))
            f.write('\t' * indention + '<pre style="overflow: auto; padding-bottom: 1.5ex; padding-top: 1ex; font-size: 15px; margin-bottom: 0ex;  margin-top: 0ex;">')
            commands_str = "\n".join(result_json["commands"])
            f.write(commands_str)
            f.write('</pre>\n')
            write_line(f, indention, result_json["invocation-note"])
            indention -= 1
            write_line(f, indention, "</div>")

            write_line(f, indention, '<div class="box">')
            indention += 1
            write_line(f, indention, '<div class="boxlabelo"><div class="boxlabelc">Execution</div></div>')
            write_line(f, indention, '<table style="margin-bottom: 0.75ex;">')
            indention += 1
            if result_json["timeout"]:
                write_line(f, indention, '<tr><td>Walltime:</td><td style="color: red;">&gt {}s (Timeout)</td></tr>'.format(result_json["time-limit"]))
            else:
                write_line(f, indention, '<tr><td>Walltime:</td><td style="tt">{}s</td></tr>'.format(result_json["wallclock-time"]))
                if "model-checking-time" in result_json:
                    write_line(f, indention, '<tr><td>Model Checking Walltime:</td><td style="tt">{}s</td></tr>'.format(result_json["model-checking-time"]))
                return_codes = []
                if "return-codes" in result_json:
                    return_codes = result_json["return-codes"]
                if result_json["execution-error"]:
                    write_line(f, indention, '<tr><td>Return code:</td><td style="tt; color: red;">{}</td></tr>'.format(", ".join([str(rc) for rc in return_codes])))
                else:
                    write_line(f, indention, '<tr><td>Return code:</td><td style="tt">{}</td></tr>'.format(", ".join([str(rc) for rc in return_codes])))
            first = True
            for note in result_json["notes"]:
                write_line(f, indention, '<tr><td>{}</td><td>{}</td></tr>'.format("Note(s):" if first else "", note))
                first = False
            indention -= 1
            write_line(f, indention, "</table>")
            indention -= 1
            write_line(f, indention, "</div>")

            pos1 = log.find("\n", log.find("Output:\n")) + 1
            pos2 = log.find("##############################Output to stderr##############################\n")
            pos_end = pos2 if pos2 >= 0 else len(log)
            log_str = log[pos1:pos_end].strip()
            if len(log_str) != 0:
                write_line(f, indention, '<div class="box">')
                indention += 1
                write_line(f, indention, '<div class="boxlabelo"><div class="boxlabelc">Log</div></div>')
                f.write("\t" * indention + '<pre style="overflow:auto; padding-bottom: 1.5ex">')
                f.write(log_str)
                write_line(f, indention, '</pre>')
                indention -= 1
                write_line(f, indention, "</div>")
            if pos2 >= 0:
                pos2 = log.find("\n", pos2) + 1
                write_line(f, indention, '<div class="box">')
                indention += 1
                write_line(f, indention, '<div class="boxlabelo"><div class="boxlabelc">STDERR</div></div>')
                f.write("\t" * indention + '<pre style="overflow:auto; padding-bottom: 1.5ex">')
                f.write(log[pos2:].strip())
                write_line(f, indention, '</pre>')
                indention -= 1
                write_line(f, indention, "</div>")
            write_line(f, indention, "</body>")
            write_line(f, indention, "</html>")
        return f_path
    
    num_cols = len(table_data[0])
    first_tool_col = num_cols - num_tool_configs

    with open (os.path.join(path, "table.html"), 'w') as tablefile:
        tablefile.write(r"""<!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>Benchmark results</title>
      <link rel="stylesheet" type="text/css" href="style.css">
      <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.10.13/css/jquery.dataTables.min.css">
      <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/buttons/1.2.4/css/buttons.dataTables.min.css">
      <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/fixedheader/3.1.2/css/fixedHeader.dataTables.min.css">

      <script type="text/javascript" language="javascript" charset="utf8" src="https://code.jquery.com/jquery-1.12.4.js"></script>
      <script type="text/javascript" language="javascript" charset="utf8" src="https://cdn.datatables.net/1.10.13/js/jquery.dataTables.min.js"></script>
      <script type="text/javascript" language="javascript" charset="utf8" src="https://cdn.datatables.net/fixedheader/3.1.2/js/dataTables.fixedHeader.min.js"></script>
      <script type="text/javascript" language="javascript" charset="utf8" src="https://cdn.datatables.net/buttons/1.2.4/js/dataTables.buttons.min.js"></script>
      <script type="text/javascript" language="javascript" charset="utf8" src="https://cdn.datatables.net/buttons/1.2.4/js/buttons.colVis.min.js"></script>

      <script>
        $(document).ready(function() {
          // Set correct file
          $("#content").load("data.html");
        } );

        function updateBest(table) {
          // Remove old best ones
          table.cells().every( function() {
            $(this.node()).removeClass("best");
          });
          table.rows().every( function ( rowIdx, tableLoop, rowLoop ) {
              var bestValue = -1
              var bestIndex = -1
              $.each( this.data(), function( index, value ){
                if (index >= """ + str(first_tool_col) + """ && table.column(index).visible()) {
    			    var text = $(value).text()
    	            if (["TO", "ERR", "INC", "MO", "NS", ""].indexOf(text) < 0) {
    				    var number = parseFloat(text);
    	                if (bestValue == -1 || bestValue > number) {
    	                  // New best value
    	                  bestValue = number;
    	                  bestIndex = index;
    	                }
    				  }
    			  }
              });
              // Set new best
              if (bestIndex >= 0) {
                $(table.cell(rowIdx, bestIndex).node()).addClass("best");
              }
          } );
      }
      </script>
    </head>
    """)
        indention = 0
        write_line(tablefile, indention, "<body>")
        write_line(tablefile, indention, "<div>")
        indention +=1
        write_line(tablefile, indention, '<table id="table" class="display">')
        indention += 1
        write_line(tablefile, indention, '<thead>')
        indention += 1
        write_line(tablefile, indention, '<tr>')
        indention += 1
        for head in table_data[0]:
            write_line(tablefile, indention, '<th>{}</th>'.format(head))
        indention -= 1
        write_line(tablefile, indention, '</tr>')
        indention -= 1
        write_line(tablefile, indention, '</thead>')
        write_line(tablefile, indention, '<tbody>')
        indention += 1

        for row in table_data[1:]:
            for cell_content in row:
                if not SHOW_UNSUPPORTED and (type(cell_content) == list and cell_content[0] == "NS") or (cell_content == "NS"):
                    cell_content = ""
                elif type(cell_content) == list:
                    logpage = create_log_page(cell_content[1])
                    style_classes = dict(TO="timeout", ERR="error", INC="incorrect", MO="memout", NS="unsupported")
                    link_attributes = "class='{}'".format(style_classes[cell_content[0]]) if cell_content[0] in style_classes else ""
                    cell_content = "<a href='{}' {}>{}</a>".format(logpage, link_attributes, cell_content[0])                        
                write_line(tablefile, indention, f'<td>{cell_content}</td>')
            indention -= 1
            write_line(tablefile, indention, '</tr>')
        indention -= 1
        write_line(tablefile, indention, '</tbody>')
        indention -= 1
        indention -= 1
        write_line(tablefile, indention, '</table>')
        write_line(tablefile, indention, "<script>")
        indention +=1
        write_line(tablefile, indention, 'var table = $("#table").DataTable( {')
        indention += 1
        write_line(tablefile, indention, '"paging": false,')
        write_line(tablefile, indention, '"autoWidth": false,')
        write_line(tablefile, indention, '"info": false,')
        write_line(tablefile, indention, 'fixedHeader: {')
        indention += 1
        write_line(tablefile, indention, '"header": true,')
        indention -= 1
        write_line(tablefile, indention, '},')
        write_line(tablefile, indention, '"dom": "Bfrtip",')
        write_line(tablefile, indention, 'buttons: [')
        indention += 1
        for columnIndex in range(first_tool_col, num_cols):
            write_line(tablefile, indention, '{')
            indention += 1
            write_line(tablefile, indention, 'extend: "columnsToggle",')
            write_line(tablefile, indention, 'columns: [{}],'.format(columnIndex))
            indention -= 1
            write_line(tablefile, indention, "},")
        tool_columns = [i for i in range(first_tool_col, num_cols)]
        for text, show, hide in zip(["Show all", "Hide all"], [tool_columns, []], [[], tool_columns]):
            write_line(tablefile, indention, '{')
            indention += 1
            write_line(tablefile, indention, 'extend: "colvisGroup",')
            write_line(tablefile, indention, 'text: "{}",'.format(text))
            write_line(tablefile, indention, 'show: {},'.format(show))
            write_line(tablefile, indention, 'hide: {}'.format(hide))
            indention -= 1
            write_line(tablefile, indention, "},")
        indention -= 1
        write_line(tablefile, indention, "],")
        indention -= 1
        write_line(tablefile, indention, "});")
        indention -= 1
        write_line(tablefile, indention, "")
        indention += 1
        write_line(tablefile, indention, 'table.on("column-sizing.dt", function (e, settings) {')
        indention += 1
        write_line(tablefile, indention, "updateBest(table);")
        indention -= 1
        write_line(tablefile, indention, "} );")
        indention -= 1
        write_line(tablefile, indention, "")
        indention += 1
        write_line(tablefile, indention, "updateBest(table);")
        indention -= 1
        write_line(tablefile, indention, "</script>")
        indention -= 1
        write_line(tablefile, indention, "</div>")
        write_line(tablefile, indention, "</body>")
        write_line(tablefile, indention, "</html>")

    with open (os.path.join(path, "style.css"), 'w') as stylefile:
        stylefile.write(r"""

    .best {
        background-color: lightgreen;
    }
    .error {
    	font-weight: bold;
    	background-color: lightcoral;
    }
    .incorrect {
        background-color: orange;
    	font-weight: bold;
    }
    .timeout {
        background-color: lightgray;
    }
    .memout {
        background-color: lightgray;
    }
    .unsupported {
        background-color: yellow;
    }
    .ignored {
        background-color: blue;
    }

    h1 {
    	font-size: 28px; font-weight: bold;
    	color: #000000;
    	padding: 1px; margin-top: 20px; margin-bottom: 1ex;
    }

    tt, .tt {
    	font-family: 'Courier New', monospace; line-height: 1.3;
    }

    .box {
    	margin: 2.5ex 0ex 1ex 0ex; border: 1px solid #D0D0D0; padding: 1.6ex 1.5ex 1ex 1.5ex; position: relative;
    }

    .boxlabelo {
    	position: absolute; pointer-events: none; margin-bottom: 0.5ex;
    }

    .boxlabel {
    	position: relative; top: -3.35ex; left: -0.5ex; padding: 0px 0.5ex; background-color: #FFFFFF; display: inline-block;
    }
    .boxlabelc {
    	position: relative; top: -3.17ex; left: -0.5ex; padding: 0px 0.5ex; background-color: #FFFFFF; display: inline-block;
    }
    """)
    
    

def save_latex(table_data, cols, header, path):
    with open(path, 'w') as latex_file:
        latex_file.write(r"""
% \setlength{\tabcolsep}{10pt}
% \renewcommand{\arraystretch}{1.2}
\begin{table}
\caption{the caption}\label{thelabel}
\begin{tabular}{@{}""")
        latex_file.write(cols)
        latex_file.write(r"""@{}}

\toprule
""")
        latex_file.write(header + "\\\\ \\midrule\endhead\n")
        for row in table_data[1:]:
            latex_file.write("\t&\t".join(row) + "\\\\\n")
        latex_file.write(r""" \bottomrule
\end{tabular}
\end{table}
""")

def parse_tool_output(execution_json):
    with open(execution_json["log"], 'r') as logfile:
        log = logfile.read()
    execution_json["notes"] = [execution_json["invocation-note"]]
    execution_json["benchmark"] = benchmarks.from_id(execution_json["benchmark-id"])
    
    assert execution_json["tool"] in TOOL_NAMES, "Error: Unknown tool '{}'".format(execution_json["tool"])
    tool = TOOL_NAMES[execution_json["tool"]]
    execution_json["configuration"] = tool.config_from_id(execution_json["configuration-id"])
    tool.parse_logfile(log, execution_json)
    
    # modify logfile
    NOTES_HEADING = "\n" + "#"*30 + " Notes " + "#"*30 + "\n"
    posEnd = log.find(NOTES_HEADING)
    if posEnd >= 0: log = log[:posEnd]
    if len(execution_json["notes"]) > 0: log += NOTES_HEADING + "\n".join(execution_json["notes"]) + "\n"
    with open(execution_json["log"], 'w') as logfile:
        logfile.write(log)   

# stores benchmark-instance specific data from the execution. Reports inconsistencies with other executions on the same instance
def process_benchmark_instance_data(benchmark_instances, execution_json):
    # gather data from this execution
    bench_id = execution_json["benchmark"]["id"]
    bench_data = OrderedDict()
    bench_data["id"] = execution_json["benchmark"]["id"]
    bench_data["name"] = execution_json["benchmark"]["name"]
    bench_data["formalism"] = execution_json["benchmark"]["model"]["formalism"]
    bench_data["type"] = execution_json["benchmark"]["model"]["type"]
    bench_data["par"] = bench_id.split("_")[2]
    bench_data["property"] = execution_json["benchmark"]["property"]["type"]
    bench_data["dim"] = execution_json["benchmark"]["property"].get("num-bnd-rew-assignments", 0)
    bench_data["states"] = execution_json["input-model"]["states"]
    if execution_json["benchmark"]["model"]["type"] != "dtmc":
        bench_data["choices"] = execution_json["input-model"]["choices"]
    if execution_json["benchmark"]["model"]["type"] == "pomdp":
        bench_data["observations"] = execution_json["input-model"]["observations"]
    bench_data["transitions"] = execution_json["input-model"]["transitions"]
    if "num-epochs" in execution_json and "result" in execution_json:
        bench_data["epochs"] = [execution_json["num-epochs"]]
    bench_data["invocations"] = [execution_json["id"]]
    
    # incorporate into existing data
    if not bench_id in benchmark_instances:
        benchmark_instances[bench_id] = bench_data
    else:
        # ensure consistency
        for key in ["id", "name", "formalism", "type", "par", "property", "dim", "states", "choices", "observations", "transitions", "num-epochs"]:
            if key in bench_data:
                if key in benchmark_instances[bench_id]:
                    if benchmark_instances[bench_id][key] != bench_data[key]:
                        print("WARN: Inconsistency with field {} between invocations \n\t{}\nand\t{}".format(key, benchmark_instances[bench_id]["invocations"], bench_data["invocations"]))
                else:
                    benchmark_instances[bench_id][key] = bench_data[key]
        # append data
        for key in ["invocations"]:
            if key in bench_data:
                if key in benchmark_instances[bench_id]:
                    benchmark_instances[bench_id][key] += bench_data[key]
                else:
                    benchmark_instances[bench_id][key] = bench_data[key]

def gather_execution_data(logdirs, silent=False):
    exec_data = OrderedDict() # Tool -> Config -> Benchmark -> Data
    benchmark_instances = OrderedDict() # ID -> data
    
    for logdir_input in logdirs:
        logdir = os.path.expanduser(logdir_input)
        if not os.path.isdir(logdir):
            print("Error: Directory '{}' does not exist.".format(logdir))

        print("\nGathering execution data for logfiles in {} ...".format(logdir))
        json_files = [ f for f in os.listdir(logdir) if f.endswith(".json") and os.path.isfile(os.path.join(logdir, f)) ]
        i = 0
        for execution_json in [ load_json(os.path.join(logdir, f)) for f in json_files ]:
            benchmark = execution_json["benchmark-id"]
            if benchmarks.from_id(benchmark) is None:
                print(f"WARN: Ignoring data for unknown benchmark {benchmark}")
                continue
            i += 1
            tool = execution_json["tool"]
            config = execution_json["configuration-id"]
            exec_data.setdefault(tool, OrderedDict())
            exec_data[tool].setdefault(config, OrderedDict())
            assert benchmark not in exec_data[tool][config], "Error: Multiple result files found for {}.{}.{}".format(tool,config,benchmark)
            execution_json["log"] = os.path.join(logdir, execution_json["log"])
            try:
                parse_tool_output(execution_json)
            except AssertionError as e:
                print("Error when parsing logfile {}:\n{}".format(execution_json["log"], e))
                continue
            exec_data[tool][config][benchmark] = execution_json
            process_benchmark_instance_data(benchmark_instances, execution_json)

    # warn for missing configs:
    if not silent:
        for t in TOOL_NAMES:
            if t not in list(exec_data.keys()) + []: print(f"WARN: no data for tool '{t}'") # no warning for tools in the given list
            else:
                for cfg in TOOL_NAMES[t].CONFIGS:
                    if cfg["id"] not in list(exec_data[t].keys()) + ["split"]: print(f"WARN: no data for {t} config '{cfg['id']}'") #no warning for configs in the given list
    return exec_data, benchmark_instances
    
def export_data(exec_data, benchmark_instances):
    SCATTER_MIN_VALUE, SCATTER_MAX_VALUE = 1, 1000
    QUANTILE_MIN_VALUE = 1
    KINDS = ["default", "scatter", "quantile", "html", "latex"]

    def scatter_special_value(i): return round(SCATTER_MAX_VALUE * (math.sqrt(2)**i))
    
    def get_result(tool, config, inst_id):
        if tool in exec_data and config in exec_data[tool] and inst_id in exec_data[tool][config]:
            return exec_data[tool][config][inst_id]
                
    def get_result_if_supported(tool, config, inst_id):
        res = get_result(tool, config, inst_id)
        if res is not None and not res["not-supported"]:
            return res
    
    def get_instances_num_supported(cfgs):
        res = Counter()
        for i in benchmarks.INSTANCES:
            res[i["id"]] = len([c for c in cfgs if get_result_if_supported(c[0], c[1], i["id"]) is not None])
        return res
    
    def get_instances_supported_by_some(cfgs):
        return [i[0] for i in get_instances_num_supported(cfgs).items() if i[1] > 0]
              
    def get_instances_supported_by_all(cfgs):
        return [i[0] for i in get_instances_num_supported(cfgs).items() if i[1] == len(cfgs)]

    def to_html(text):
        return html.escape(str(text))

    def to_latex(value, data_kind = None):
        if type(value) == int:
            v = f"{value:.4g}"
            if "e+" in v: v = "{} {{\cdot}} 10^{{{}}}".format(round(float(v[:v.find("e+")])), int(v[v.find("e+")+2:]))
        elif type(value) == bool:
            v = "yes" if value else "no"
        elif type(value) == list:
            if all(type(e) == int for e in value):
                if min(value) == max(value):
                    v = to_latex(min(value))
                else:
                    v = "{}..{}".format(to_latex(min(value)), to_latex(max(value)))
        elif type(value) == str and value.startswith("(") and value.endswith(")"):
            v = "{}".format(value[1:-1])
        elif type(value) == str and data_kind == "name":
            v = f"\\model{{{value}}}"
        elif type(value) == str and data_kind == "par":
            v = value.replace("_", "\_")
        elif type(value) == float:
            v = f"{value:.1f}"
        else:
            v = value
        return v if data_kind is None else f"${v}$"
            
    def get_cell_content(column, inst, kind):
        assert kind in KINDS, f"Invalid kind for cell content: {kind}"
        value = None
        # first check if the column refers to a tool config
        tool = column[0]
        if tool in TOOL_NAMES: # the column is assumed to be a [tool, config, data_key] list, where data_key is the cell content key
            res = get_result_if_supported(tool, column[1], inst)
            if res is None:
                if kind in ["default", "html"]:
                    value = "NS"
                elif kind in ["scatter"]:
                    value = scatter_special_value(2)
                elif kind in ["latex"]:
                    value = ""
                elif kind in ["quantile"]:
                    value = math.inf
            elif res["timeout"] == True:
                if kind in ["default", "html", "latex"]:
                    value = "TO"
                elif kind in ["scatter"]:
                    value = scatter_special_value(1) # TO
                elif kind in ["quantile"]:
                    value = math.inf
            elif res["memout"]:
                if kind in ["default", "html", "latex"]:
                    value = "MO"
                elif kind in ["scatter"]:
                    value = scatter_special_value(1)
                elif kind in ["quantile"]:
                    value = math.inf
            elif res["expected-error"]:
                if kind in ["default", "html", "latex"]:
                    value = "ERR"
                elif kind in ["scatter"]:
                    value = scatter_special_value(1)
                elif kind in ["quantile"]:
                    value = math.inf
            elif "result" in res:
                value = res[column[2]]
                if "time" in column[2]:
                    if kind in ["html"]:
                        value = f"{value:.1f}"
                    elif kind in ["latex"]:
                        if value < 1.0:
                            value = r"\textless 1"
                        elif value < 100:
                            value = f"{value:.1f}"
                        else:
                            value = f"{value:.0f}"
                    elif kind in ["scatter"]:
                        value = max(SCATTER_MIN_VALUE, min(SCATTER_MAX_VALUE, value))
                    elif kind in ["quantile"]:
                        value = max(QUANTILE_MIN_VALUE, value)
            if kind == "html":
                res = get_result(tool, column[1], inst)
                if res is not None:
                    value = [value, res]
                if "result" in res:
                    value[0] += to_html(" / {}".format(res["result"]))
        else: # column[0] is a key in benchmark_instances, column[1] is either not present or a function that applies a transformation
            if column[0] in benchmark_instances[inst]:
                value = benchmark_instances[inst][column[0]]
            else: # info not available
                if kind in ["scatter", "quantile"]:
                    value = "nan"
                else:
                    value = "" 
            if len(column) > 1:
                value = column[1](value)
            elif kind in ["latex"]:
                value = to_latex(value, column[0])
            elif kind in ["scatter"] and type(value) == list:
                if len(value) == 0: value = "nan"
                else: value = sum(value) / len(value) # average
            if type(value) == Counter:
                value = ", ".join([f"{k}: {v}" for k,v in value.items()])
            value = f"{value}"
        assert value is not None, f"No value found for column {column}, and instance {inst} (kind {kind})"
        return value
        
    def create_cells(columns, cfgs, kind):
        if kind == "quantile":
            rows = get_instances_supported_by_all(cfgs)
            header = ["i"] + [f"{c[0]}.{c[1]}" for c in columns[-len(cfgs):]]
            cells = [header] + [[i+1] for i in range(len(rows))]
            for c in columns[-len(cfgs):]:
                c_runtimes = sorted([get_cell_content(c, inst, kind) for inst in rows])
                for j in range(len(c_runtimes)):
                    cells[j+1].append(c_runtimes[j] if c_runtimes[j] != math.inf else "nan")
            return cells
        else:
            header = [c[0] for c in columns[:-len(cfgs)]] + [f"{c[0]}.{c[1]}" for c in columns[-len(cfgs):]]
            rows = get_instances_supported_by_some(cfgs)
            cells = [header]
            for inst in rows:
                cells.append([])
                for c in columns:
                    cells[-1].append(get_cell_content(c, inst, kind))
                if kind == "latex":
                    # mark the fastest runtime
                    j_best = []
                    val_best = None
                    for j in range(len(columns) - len(cfgs), len(columns)):
                        try:
                            val_curr = 0.0 if r"\textless" in cells[-1][j] else float(cells[-1][j])
                            if val_best is None or val_best >= val_curr:
                                if val_best == val_curr:
                                    j_best.append(j)
                                else:
                                    j_best =[j]
                                    val_best = val_curr
                        except ValueError: continue
                    for j in j_best:
                        cells[-1][j] = f"\\textbf{{{cells[-1][j]}}}"                        
            return cells
    
    def export_data_for_kind(kind):
        # benchmark info columns
        cols = [["name"], ["par"], ["states"], ["choices"], ["observations"], ["property"], ["dim"]]
        latex_cols = [r"\multicolumn{2}{c}{model}", r"$|S|$", r"$|Act|$", r"$|Z|$", "Prop", "dim"]
        latex_col_aligns = "ccrrrcc"
        cfgs = []
        for tool in TOOLS:
            cfgs += [[tool.NAME, c["id"]] for c in tool.CONFIGS]
        # extend columns with configuration data
        cols += [c + ["wallclock-time"] for c in cfgs]
        latex_cols += [config_from_id(c[0], c[1])["latex"] for c in cfgs]
        latex_col_aligns += "r" * len(cfgs)
        latex_header = "\n& ".join(latex_cols)
        
        # create and export different kinds of data
        cells = create_cells(cols, cfgs, kind)
        if kind in ["default", "scatter", "quantile"]:
            save_csv(cells, os.path.join(OUT_DIR, f"{kind}.csv"))
        elif kind == "html":
            save_html(cells, len(cfgs), os.path.join(OUT_DIR, f"table"))
        elif kind == "latex":
            save_latex(cells, latex_col_aligns, latex_header, os.path.join(OUT_DIR, f"table.tex"))
        else:
            assert False, f"Unhandled kind: {kind}"
    
    # invoke generation for all kinds
    for kind in KINDS: export_data_for_kind(kind)
    
 
if __name__ == "__main__":
    print("Benchmarking tool.")
    print("This script gathers data of executions and exports them in various ways.")
    print("Usages:")
    print("python3 {} path/to/first/logfiles/ path/to/second/logfiles/ ...    reads from multiple log file directories '".format(sys.argv[0]))
    print("")
    if (len(sys.argv) == 2 and sys.argv[1] in ["-h", "-help", "--help"]):
        exit(1)

    logdirs = sys.argv[1:]

    print("Selected log dir(s): {}".format(", ".join(logdirs)))
    print("")
    
    exec_data, benchmark_instances = gather_execution_data(logdirs)
    if not os.path.exists(OUT_DIR): os.makedirs(OUT_DIR)
    save_json(exec_data, os.path.join(OUT_DIR, "execution-data.json"))
    save_json(benchmark_instances, os.path.join(OUT_DIR, "benchmark-data.json"))
    
    benchmark_instances = OrderedDict(sorted(benchmark_instances.items(), key=lambda item: item[0]))
    print("Found Data for {} benchmarks".format(len(benchmark_instances)))
    
    export_data(exec_data, benchmark_instances)
