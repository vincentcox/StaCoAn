$(document).ready(function(){
	
	//for lootbox
	
  
  
var node_list  = {}; // contains the looted stuff
  for (var i = 0; i < localStorage.length; i++){
	  if (localStorage.key(i).startsWith("loot_")){
			var localstor = localStorage.key(i).split("_")[1]
			while (( localstor.length % 4 ) != 0){
				localstor += "=";
			}
			console.log(localstor);
			var raw = atob(localstor).split("|||");
			//atob(localStorage.getItem(localStorage.key(i))).split("|");
			node_list[raw[0]+"|||"+raw[1]]=1;
			console.log(raw[0]+raw[1]);
	  }
	}
	console.log("list");
	console.log(node_list);
	
	var tree = $("#tree").fancytree("getTree");
  tree.visit(function(node){
		  if (node.key+"|||"+node.title in node_list ){
			  console.log(node.key+"///"+node.title+"|||"+node_list[node.key]);
			  node.addClass("looted");
		  }
    
	//console.log(btoa(node.key+node.title));

  });
	
  
  
 
  
  // automatic code detection
  $(".fancytree-container").attr("style", "overflow: scroll; overflow-y: auto; padding:0px !important;");
  $(".fancytree-container").addClass("card-content");
  $("#tree").addClass("card z-depth-5");
  //$("#tree").css({ display: "block" });


	fileHighlightCustom = function() {


		var Extensions = {
			'js': 'javascript',
			'py': 'python',
			'rb': 'ruby',
			'ps1': 'powershell',
			'psm1': 'powershell',
			'sh': 'bash',
			'bat': 'batch',
			'h': 'c',
			'tex': 'latex'
		};

		Array.prototype.slice.call(document.querySelectorAll('pre[data-src]')).forEach(function (pre) {
			var src = pre.getAttribute('data-src');

			var language, parent = pre;
			var lang = /\blang(?:uage)?-(?!\*)(\w+)\b/i;
			while (parent && !lang.test(parent.className)) {
				parent = parent.parentNode;
			}

			if (parent) {
				language = (pre.className.match(lang) || [, ''])[1];
			}

			if (!language) {
				var extension = (src.match(/\.(\w+)$/) || [, ''])[1];
				language = Extensions[extension] || extension;
			}
			try {
			pre.firstElementChild.className = 'language-' + language;
			}
			catch(err) {
			}
		});
	}
	
	fileHighlightCustom();
	Prism.highlightAll();
	$('ul.tabs').tabs();
  

});


function removeUnimportantFiles(){
[].forEach.call(document.querySelectorAll('.grade-0'), function (el) {
  el.parentNode.outerHTML = '';
});


}