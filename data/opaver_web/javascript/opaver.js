var global_overview_pwy = {
	"01100": "Metabolic pathways",
	"01110": "Biosynthesis of secondary metabolites",
	"01120": "Microbial metabolism in diverse environments",
	"01200": "Carbon metabolism",
	"01210": "2-Oxocarboxylic acid metabolism",
	"01212": "Fatty acid metabolism",
	"01230": "Biosynthesis of amino acids",
	"01220": "Degradation of aromatic compounds"
};

//
// addSelector
// 

function addSelector(mapdiv, mapid, dir, tpdir){
	// default time point settings file
	var settings_json = dir+'/settings.json';
	//var selectdivdom = $('<div class="ui-field-contain">');
	selectdivdom = $('<fieldset data-role="controlgroup" data-type="horizontal" data-mini="true">');
	selectdivdom.append($('<legend>Select a timepoint and map:</legend>'));

	// add auto play switch
	selectdom = $('<select id="autoplay-switch" data-mini="true"><option value="off">Autoplay OFF</option><option value="3">Autoplay ON (3s)</option><option value="6">Autoplay ON (6s)</option><option value="10">Autoplay ON (10s)</option></select>');
	selectdom.on("change",function(){
		if( this.value != "off" ){
			var tppool = []
			var idx = 0
			var cnt = 0

			if( interval ){
				window.clearInterval(interval);
			}

			$("#timepoint-selector option").each(function(){
				tppool.push(this.value)
				if( $('#timepoint-selector').val() == this.value ){
					cnt = idx;
				}
				idx++
			});

			interval = window.setInterval( function() {
				$('#timepoint-selector').val(tppool[(cnt+1)%idx]).change()
				cnt++;
			}, this.value*1000 );

			$(this).parent().css({"background-color": "#38c", "border-color": "#38c", "color": "#fff", "text-shadow": "0 1px 0 #059"});
		}
		else{
			$(this).parent().removeAttr( 'style' );
			window.clearInterval(interval);
		}
	});
	selectdivdom.append(selectdom);

	// Time point selector
	var loadJSON = $.getJSON( settings_json, function(data){
		var selectdom = $('<select name="timepoint-selector" id="timepoint-selector" data-mini="true">');
		$.each(data, function(idx, tpinfo){
			select_flag=""
			if( tpdir == tpinfo.dir){
				select_flag="selected";
			}
			var odom = $('<option id="tp_selec'+idx+'" value="'+tpinfo.dir+'" '+select_flag+' >'+tpinfo.name+' ('+tpinfo.desc+')</option>');
			selectdom.append(odom);
		});

		selectdom.on( "change", function(){
			if( this.value ){
				drawMap(mapdiv, $('#pathway-selector').val(), showicon, org, dir, this.value, false);
			}
		});

		selectdivdom.append(selectdom);				
	});

	// KEGG map selector
	var pwytab = dir+'/'+tpdir+'/exp_pathway.txt';
	// retrieve the list of all KEGG map at the time point
	var loadEXPPWY = $.get( pwytab, function(data){
		var selectdom = $('<select name="pathway-selector" id="pathway-selector" data-mini="true">');
		var tsv = $.tsv.parseRows(data);
		$.each(tsv, function(idx,pwy){
			var note = "";
			if( typeof(global_overview_pwy[pwy[0]]) != "undefined" ){ note = " [View only]"; }
			var	select_flag="";
			if( mapid == pwy[0] ){ select_flag="selected"; }
			if( typeof(pwy[1]) != "undefined" ){
				var odom = $('<option id="map_selec'+pwy[0]+'" value="'+pwy[0]+'" '+select_flag+' >'+pwy[0]+' '+pwy[2]+' ('+pwy[1]+') '+note+'</option>');
				selectdom.append(odom);
			}
		});

		selectdom.on("change",function(){
			if( this.value ){
				drawMap(mapdiv, this.value, showicon, org, dir, $('#timepoint-selector').val(), true);
			}
		});
		selectdivdom.append(selectdom);
	});

	$.when( loadJSON, loadEXPPWY ).done(function ( v1, v2 ) {
		$("#"+mapdiv).before(selectdivdom);
		$("select").selectmenu({ inline: true, nativeMenu: true })
	});
}

//
// drawMap
// 

function drawMap(mapdiv, mapid, showicon, org, dir, tp, loadKGML) {
	mapid      = mapid;                               //initial map
	showicon   = showicon || 2;                       //show number of genes icon if number of genes > gene_show
	org        = org || "ko";                         //default organism
	type       = org === "ko" ? "ortholog" : "gene";  //enzyme rect type
	var mapxml = dir+'/'+tp+'/'+org+mapid+'.xml';
	var expjson = dir+'/'+tp+'/'+org+mapid+'.exp.json';
	var mapImg;
	var kgml;

	//clean tooltipster and KEGG map
	$("#"+mapdiv+" a").remove();

	//loading background pathway map		
	//$("#"+mapdiv).width(0);
	//$("#"+mapdiv).height(0);

	if( $("#map-image").length ){
		mapImg = $("#map-image")
	}
	else{
		mapImg = $("<img id='map-image'>");
		$("#"+mapdiv).append(mapImg);
	}
	
	mapImg.attr("src", dir+"/"+tp+'/'+org+mapid+".pathview.multi.png");

	mapImg.load(function(){
		var originalWidth = $("#"+mapdiv+" img")[0].naturalWidth; 
		var originalHeight = $("#"+mapdiv+" img")[0].naturalHeight;
		$("#"+mapdiv).width(originalWidth);
		$("#"+mapdiv).height(originalHeight);
		$("#"+mapdiv+" div.main_title").remove();

		//create map title
		var titledom = $('<div class="main_title">');
		var note = "";
		if( typeof(global_overview_pwy[mapid]) != "undefined" ){ note = " [Global and overview pathways are not supported]"; }
		titledom.html("Pathway: "+mapid+note+", Timepoint: "+tp);

		if( prev_mapid.length > 0 ){
			var backbtn = $('<a id="back_btn" href="#" data-mini="true" class="ui-btn ui-icon-back ui-btn-icon-notext ui-corner-all">');
			backbtn.on("click",function(){
				mapid = prev_mapid.pop(); //pop itself
				mapid = prev_mapid.pop(); //pop last map id
				if(mapid){
					$('#pathway-selector').val(mapid).change()
				}
			});
			titledom.append(backbtn);
		}

		$("#"+mapdiv).append(titledom);
	});

	// load KGML
	var loadKGML = $.ajax({
		type: "get",
		url: mapxml,
		dataType: "xml",
		beforeSend: function(){
			$.mobile.loading( "show", {
					text: "Loading KEGG map"+mapid+"...",
					textVisible: false,
					theme: "b"
			});
		},
		complete: function(){
			$.mobile.loading( "hide" );
		},
		success: function(data) {
			kgml = data
		},
		error: function() {
			var popupdom = $('<div data-role="popup" id="popupDialog" data-overlay-theme="b" data-theme="b" data-dismissible="false" style="max-width:400px;">');
				var popupheader = $('<div data-role="header" data-theme="a">').append($('<h2>Pathway Not Available</h2>'));
			popupdom.append(popupheader);
			
			var popmain = $('<div role="main" class="ui-content">')
						.append($('<h3 class="ui-title">Global and overview pathways are not supported.</h3>'))
						.append($('<p>Press OK to bring you back.</p>'))
						.append($('<a href="#" class="ui-btn ui-corner-all ui-shadow ui-btn-inline ui-btn-b" data-rel="back">Ok</a>'));
			popupdom.append(popmain);
			popupdom.popup({
				afterclose: function( event, ui ) {
					mapid = prev_mapid.pop();
					drawMap(mapdiv, mapid, showicon, org, dir, tp, true)
				}
			});
			//$("#"+mapdiv).append(popupdom);
			popupdom.popup('open');
		}
	});

	//load expression/annotation json file
	$.ajax({
		type: "get",
		url: expjson,
		dataType: "json",
		beforeSend: function(){
			$.mobile.loading( "show", {
					text: "Loading KEGG map"+mapid+"...",
					textVisible: false,
					theme: "b"
			});
		},
		complete: function(){
			$.mobile.loading( "hide" );
		},
		success: function(annojson) {
			// Find all graphics object in KGML
			$.when( loadKGML ).done(function(){
				$(kgml).find( "graphics" ).each(function(){
					var entry_type = $(this).parent().attr("type");
					var graphic_type = $(this).attr("type");

					// SKIPPING any lines
					if( graphic_type == 'line' ){return true;}

					// dealing with compund graphic
					if( entry_type == "compound" ){
						var url = $(this).parent().attr("link");
						var cid = $(this).attr("name");
						var x = $(this).attr("x")-$(this).attr("width")/2;
						var y = $(this).attr("y")-$(this).attr("height")/2;
						var dom = "<a class='compound-area' href='"+url+"' target='new' title='cpd: "+cid+"' style='left:"+x+"px;top:"+y+"px;'></a>";
						var jdom = $(dom);
						jdom.appendTo($("#"+mapdiv));

						var tooltipcontent = $( '<div>' );

						if( typeof(annojson[cid]) == 'undefined' ){
							tooltipcontent
								.append( $('<span class="tag-label">'+cid+'</span>') )
								.append( $('<img src="http://rest.kegg.jp/get/'+cid+'/image"></img>') );
						}
						else{
							var idtag = $('<span class="tag-label">'+cid+'</span>');
							tooltipcontent.append(idtag);

							var tabledom = $('<table data-role="table" data-mode="reflow" class="gene-info ui-responsive">');
							var tbodydom = $('<tbody>');
							$('<tr>')
								.append( $('<td>').html('Name') )
								.append( $('<td>').html( annojson[cid].info.name ) )
								.appendTo(tbodydom);
							
							var pathwayTd = $('<td>');
							var pwys = annojson[cid].info.pathway.split(", ");
							$.each( pwys, function(idx, pwy){
								$('<a data-ajax="false" style="margin-right:0.5em">')
									.html(pwy)
									.on("click",function(){ if(pwy!=mapid){drawMap(mapdiv, pwy, showicon, org, dir, tp, true)}})
									.appendTo( pathwayTd );
							});

							$('<tr>')
								.append( $('<td>').html('Pathway') )
								.append( pathwayTd )
								.appendTo(tbodydom);
							$('<tr>')
								.append( $('<td>').html('Desc') )
								.append( $('<td>').html( annojson[cid].info.name ) )
								.appendTo(tbodydom);
							$('<tr>')
								.append( $('<td>').html('Formula') )
								.append( $('<td>').html( '<img src="http://rest.kegg.jp/get/'+cid+'/image"></img>' ) )
								.appendTo(tbodydom);
							
							tabledom.table();
							tabledom.append(tbodydom);
							tooltipcontent.append(tabledom);
							
							if( $(annojson[cid].cpd).length ){
								var tabledom = $('<table data-role="table" data-mode="reflow" class="gene-info ui-responsive">');
								var theaddom = $('<thead>');
								$('<tr>').append( $('<th>').html('Compound') )
										.append( $('<th>').html('FC') )
										//.append( $('<th>').html('P-value') )
										.appendTo(theaddom);
								
								var tbodydom = $('<tbody>');
								$.each(annojson[cid].cpd, function( name, cinfo){
									$('<tr>').append( $('<td>').html( name ) )
											.append( $('<td>').html( cinfo.logfc ) )
											//.append( $('<td>').html( cinfo.pvalue ) )
											.appendTo(tbodydom);
								});

								tabledom.table();
								tabledom.append(theaddom);
								tabledom.append(tbodydom);
								tooltipcontent.append(tabledom);
							}
						}
						jdom.tooltipster({content: tooltipcontent, arrow: false, offsetX: 4, offsetY: 20, position: 'right', interactive: true});
					}
					// dealing with ortholog/enzyme graphics
					else if ( entry_type == "ortholog" ){
						var url = $(this).parent().attr("link");
						var name = $(this).parent().attr("name");
						var x = $(this).attr("x")-1-$(this).attr("width")/2;
						var y = $(this).attr("y")-2-$(this).attr("height")/2;
						var dom;
						dom = "<a class='enzyme-area' alt='"+name+"' href='"+url+"' target='new' title='"+name+"' style='left:"+x+"px;top:"+y+"px;'></a>";
						var jdom = $(dom);
						jdom.tooltipster({interactive: true});
						jdom.appendTo($("#"+mapdiv));

						//check if tooltip needs
						var regex = new RegExp(org+":", "g")
						var idstring = name.replace(regex, "");
						var idarray = idstring.split(" ");
						var ids = $.map( idarray, function( id, i ) {
							if( typeof(annojson[id]) != 'undefined' ){
								return id;
							}
						});

						var tooltipcontent = $( '<div>' );
						var tranIcon       = $( '<div class="gene-number-icon tran-number">' ).html(0);
						var protIcon       = $( '<div class="gene-number-icon prot-number">' ).html(0);

						$.each(ids, function(index, id){
							//add transcriptomic gene number icon
							if( $(annojson[id].tran).length ){
								var x=jdom.width()-6;
								var y=-8;
								contentdom = tranIcon;
								var num = contentdom.html();
								var tolnum = parseInt(num) + Object.keys(annojson[id].tran).length;
								contentdom.html( tolnum );
								contentdom.css( "left", x+"px" );
								contentdom.css( "top", y+"px" );
								
							}
							//add proteomic gene number icon
							if( $(annojson[id].prot).length ){
								var x=-6;
								var y=-8;
								contentdom = protIcon;
								var num = contentdom.html();
								var tolnum = parseInt(num) + Object.keys(annojson[id].prot).length;
								contentdom.html( tolnum );
								contentdom.css( "left", x+"px" );
								contentdom.css( "top", y+"px" );
							}

							//tooltip content
							//KEGG ID information
							var idtag = $('<span class="tag-label">'+org+':'+id+'</span>');
							idtag.on("click", function(){
								$("#"+mapdiv).find("a.enzyme-area.glow").removeClass("glow");
								$("#"+mapdiv).find("a.enzyme-area[alt*='"+id+"']").addClass("glow");
							});

							tooltipcontent.append(idtag);
							var tabledom = $('<table data-role="table" data-mode="reflow" class="gene-info ui-responsive">');
							var tbodydom = $('<tbody>');
							$('<tr>')
								.append( $('<td>').html('Name') )
								.append( $('<td>').html( annojson[id].info.name ) )
								.appendTo(tbodydom);
							
							var pathwayTd = $('<td>');
							var pwys = annojson[id].info.pathway.split(", ");
							$.each( pwys, function(idx, pwy){
								$('<a data-ajax="false" style="margin-right:0.5em">')
									.html(pwy)
									.on("click",function(){ if(pwy!=mapid){drawMap(mapdiv, pwy, showicon, org, dir, tp, true)}})
									.appendTo( pathwayTd );
							});

							$('<tr>')
								.append( $('<td>').html('Pathway') )
								.append( pathwayTd )
								.appendTo(tbodydom);
							$('<tr>')
								.append( $('<td>').html('Desc') )
								.append( $('<td>').html( annojson[id].info.definition ) )
								.appendTo(tbodydom);
							tabledom.table();
							tabledom.append(tbodydom);
							tooltipcontent.append(tabledom);
							
							//add proteomics gene info
							if( $(annojson[id].prot).length ){
								tooltipcontent.append($('<span>').html("Proteomics ("+Object.keys(annojson[id].prot).length+")"));

								var tabledom = $('<table data-role="table" data-mode="reflow" class="gene-info ui-responsive">');
								var theaddom = $('<thead>');
								$('<tr>').append( $('<th>').html('Gene') )
										//.append( $('<th>').html('P-value') )
										.append( $('<th>').html('FC') )
										.appendTo(theaddom);
								
								var tbodydom = $('<tbody>');
								$.each(annojson[id].prot,function(gene,ginfo){
									var url_gene = '<a href="https://www.ncbi.nlm.nih.gov/gene/?term='+gene+'" target="_new">'+gene+'</a>';
									$('<tr>').append( $('<td>').html( url_gene ) )
											//.append( $('<td>').html( ginfo.pvalue ) )
											.append( $('<td>').html( ginfo.logfc ) )
											.appendTo(tbodydom);
								});

								tabledom.table();
								tabledom.append(theaddom);
								tabledom.append(tbodydom);
								tooltipcontent.append(tabledom);
							}

							//add transcriptomic gene info
							if( $(annojson[id].tran).length ){
								tooltipcontent.append($('<span>').html("Transcriptomics ("+Object.keys(annojson[id].tran).length+")"));

								var tabledom = $('<table data-role="table" data-mode="reflow" class="gene-info ui-responsive">');
								var theaddom = $('<thead>');
								$('<tr>').append( $('<th>').html('Gene') )
										//.append( $('<th>').html('P-value') )
										.append( $('<th>').html('FC') )
										.appendTo(theaddom);
								
								var tbodydom = $('<tbody>');
								$.each(annojson[id].tran,function(gene,ginfo){
									var url_gene = '<a href="https://www.ncbi.nlm.nih.gov/gene/?term='+gene+'" target="_new">'+gene+'</a>';
									$('<tr>').append( $('<td>').html( url_gene ) )
											//.append( $('<td>').html( ginfo.pvalue ) )
											.append( $('<td>').html( ginfo.logfc ) )
											.appendTo(tbodydom);
								});

								tabledom.table();
								tabledom.append(theaddom);
								tabledom.append(tbodydom);
								tooltipcontent.append(tabledom);
							}

							if( ids.length && typeof global_overview_pwy[mapid] === "undefined" ){
								if( parseInt(tranIcon.html()) >= showicon ){
									jdom.append(tranIcon)
								}
								if( parseInt(protIcon.html()) >= showicon ){
									jdom.append(protIcon)
								}
								jdom.tooltipster('destroy');
								jdom.tooltipster({content: tooltipcontent, arrow: false, interactive: true, offsetY: -100, position: 'right'});
							}
						});
					}
					//dealing with maps graphics //skip the title block of current map
					else if ( entry_type == "map" && !$(this).attr("name").startsWith("TITLE") ){
						var name = $(this).attr("name");
						var url = $(this).parent().attr("link");
						var entry_name = $(this).parent().attr("name");
						var mapid = entry_name.replace( "path:"+org, "");
						var width = $(this).attr("width")
						var height = Number($(this).attr("height"))+2
						var x = $(this).attr("x")-width/2;
						var y = $(this).attr("y")-height/2;
						
						var jdom = $("<a class='map-area' title='"+name+"' style='left:"+x+"px;top:"+y+"px;width:"+width+"px;height:"+height+"px;'></a>");
						var tooltipcontent = $('<div>');

						if( $('#pathway-selector option[value="'+mapid+'"]').length ){
							jdom.on("click",function(){ $('#pathway-selector').val(mapid).change() })
							tooltipcontent
								.append( $('<span class="tag-label">'+mapid+": "+name+'</span>') )
								.append( $('<img src="'+dir+"/"+tp+'/'+org+mapid+'.pathview.multi.png" style="width: 500px; height: auto"></img>') );
						}
						else{
							tooltipcontent
								.append( $('<span class="tag-label">'+mapid+": "+name+'</span>') )
								.append( $('<div>Not available</div>') );
						}

						jdom.appendTo($("#"+mapdiv));
						jdom.tooltipster({content: tooltipcontent, arrow: false, interactive: true, offsetY: -100, position: 'right'});
					}
				});
			});
		},
		error: function() {
			alert( "ERROR: Failed to read json file from "+expjson+"." );
		}
	});

	//save mapid; skip if current map id is same as the last one (autoplay)
	if( prev_mapid[prev_mapid.length-1] != mapid ){
		prev_mapid.push(mapid);
	}
}

function GetURLParameter(sParam)
{
	var sPageURL = window.location.search.substring(1);
	var sURLVariables = sPageURL.split('&');
	for (var i = 0; i < sURLVariables.length; i++) 
	{
		var sParameterName = sURLVariables[i].split('=');
		if (sParameterName[0] == sParam) 
		{
			return sParameterName[1];
		}
	}
}