$(document).ready(function(){
var node_list  = {};
for (var i = 0; i < localStorage.length; i++){
	  if (localStorage.key(i).startsWith("loot_")){
			var raw = atob(localStorage.key(i).split("_")[1]).split("|||");
			//atob(localStorage.getItem(localStorage.key(i))).split("|");
			//console.log(atob(localStorage.getItem(localStorage.key(i))));
			node_list[raw[0]+"|||"+raw[1]+"|||"+raw[2]+"|||"+raw[3]+"|||"+raw[4]+"|||"+raw[5]]=atob(localStorage.getItem(localStorage.key(i)));
	  }
	}
	console.log(node_list);
	
	// Build loot view.
	for (node in node_list){
		console.log(node);
		var html = ""
		html += "<div class=\"chip col\"><i class=\"material-icons\">attach_file</i><a href=\"html/view_source.html?file="
		html += node.split("|||")[0];
		html += "\" target=\"_blank\">";
		html += node.split("|||")[0];
		html += "</a></div>";
		html += "<div class='row l2'><div class='card'><div class='card-content'>";
		html += "<div class=\"valign-wrapper\"><i class=\"material-icons medium grade-";
		html += node.split("|||")[2];
		html += "\">report</i><h5>";
		html += node.split("|||")[3];
		html += "</h5></div>";
		html +=  "<pre data-src='"+node.split("|||")[0]+"' class=\"code line-numbers\" data-start=\""+node.split("|||")[5]+"\" data-line=\""+node.split("|||")[4]+"\"><code class=\"language-css\">"+node_list[node]+"</code></pre>";
		html += "</div></div></div>";
		$("#lootbox").append(html);
	}
	
	Prism.highlightAll();
});

