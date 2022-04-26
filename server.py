#!/usr/bin/env python3
import sys
import uuid
import time
import json
import base64
from pathlib import Path
from pprint import pprint
import tempfile
import zipfile
import shutil
import requests
from binascii import b2a_hex
from copy import deepcopy

import jwt
import pytz
import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from ulid import ULID

from sanic import Sanic
from sanic import Blueprint
from sanic.response import html as sanic_html
from sanic.response import raw as sanic_raw
from sanic.response import json as sanic_json
from sanic.response import file as sanic_file
from sanic.response import file_stream as sanic_file_stream
from sanic.response import stream as sanic_stream
from sanic.request import Request

import random
import genanki
import markdown

def read_text( file_path ):
	with open( file_path ) as f:
		return f.read().splitlines()
		#return f.read()

def generate_model_id():
	return random.randrange( 1 << 30 , 1 << 31 )

# https://ankiweb.net/shared/info/1087328706
katex_markdown_front = """

<div id="front"><pre>{{Front}}</pre></div>

<script>
	var getResources = [
		getCSS("_katex.css", "https://cdn.jsdelivr.net/npm/katex@0.12.0/dist/katex.min.css"),
		getCSS("_highlight.css", "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.0.1/styles/default.min.css"),
		getScript("_highlight.js", "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.0.1/highlight.min.js"),
		getScript("_katex.min.js", "https://cdn.jsdelivr.net/npm/katex@0.12.0/dist/katex.min.js"),
		getScript("_auto-render.js", "https://cdn.jsdelivr.net/gh/Jwrede/Anki-KaTeX-Markdown/auto-render-cdn.js"),
		getScript("_markdown-it.min.js", "https://cdnjs.cloudflare.com/ajax/libs/markdown-it/12.0.4/markdown-it.min.js"),
				getScript("_markdown-it-mark.js","https://cdn.jsdelivr.net/gh/Jwrede/Anki-KaTeX-Markdown/_markdown-it-mark.js")
	];
		Promise.all(getResources).then(() => getScript("_mhchem.js", "https://cdn.jsdelivr.net/npm/katex@0.13.11/dist/contrib/mhchem.min.js")).then(render).catch(show);


	function getScript(path, altURL) {
		return new Promise((resolve, reject) => {
			let script = document.createElement("script");
			script.onload = resolve;
			script.onerror = function() {
				let script_online = document.createElement("script");
				script_online.onload = resolve;
				script_online.onerror = reject;
				script_online.src = altURL;
				document.head.appendChild(script_online);
			}
			script.src = path;
			document.head.appendChild(script);
		})
	}

	function getCSS(path, altURL) {
		return new Promise((resolve, reject) => {
			var css = document.createElement('link');
			css.setAttribute('rel', 'stylesheet');
			css.type = 'text/css';
			css.onload = resolve;
			css.onerror = function() {
				var css_online = document.createElement('link');
				css_online.setAttribute('rel', 'stylesheet');
				css_online.type = 'text/css';
				css_online.onload = resolve;
				css.onerror = reject;
				css_online.href = altURL;
				document.head.appendChild(css_online);
			}
			css.href = path;
			document.head.appendChild(css);
		});
	}


	function render() {
		renderMath("front");
		markdown("front");
		show();
	}

	function show() {
		document.getElementById("front").style.visibility = "visible";
	}

	function renderMath(ID) {
		let text = document.getElementById(ID).innerHTML;
		text = replaceInString(text);
		document.getElementById(ID).textContent = text;
		renderMathInElement(document.getElementById(ID), {
			delimiters:  [
				{left: "$$", right: "$$", display: true},
				{left: "$", right: "$", display: false}
			],
			throwOnError : false
		});
	}

	function markdown(ID) {
		let md = new markdownit({typographer: true, html:true, highlight: function (str, lang) {
							if (lang && hljs.getLanguage(lang)) {
								try {
									return hljs.highlight(str, { language: lang }).value;
								} catch (__) {}
							}

							return ''; // use external default escaping
						}}).use(markdownItMark);
		let text = replaceHTMLElementsInString(document.getElementById(ID).innerHTML);
		text = md.render(text);
		document.getElementById(ID).innerHTML = text.replace(/&lt;\/span&gt;/gi,"\\\\");
	}
	function replaceInString(str) {
		str = str.replace(/<[\/]?pre[^>]*>/gi, "");
		str = str.replace(/<br\s*[\/]?[^>]*>/gi, "\\n");
		str = str.replace(/<div[^>]*>/gi, "\\n");
		// Thanks Graham A!
		str = str.replace(/<[\/]?span[^>]*>/gi, "")
		str.replace(/<\/div[^>]*>/g, "\\n");
		return replaceHTMLElementsInString(str);
	}

	function replaceHTMLElementsInString(str) {
		str = str.replace(/&nbsp;/gi, " ");
		str = str.replace(/&tab;/gi, "	");
		str = str.replace(/&gt;/gi, ">");
		str = str.replace(/&lt;/gi, "<");
		return str.replace(/&amp;/gi, "&");
	}
</script>
"""

# somehow we can't use python format strings to edit cdn urls ???
# tried double escape curly braces and everything ... anki
katex_markdown_back = """

<div style="text-align: left;" id="back"><pre>{{Back}}</pre></div>

<script>
	var getResources = [
		getCSS("_katex.css", "https://cdn.jsdelivr.net/npm/katex@0.12.0/dist/katex.min.css"),
		getCSS("_highlight.css", "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.0.1/styles/default.min.css"),
		getScript("_highlight.js", "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.0.1/highlight.min.js"),
		getScript("_katex.min.js", "https://cdn.jsdelivr.net/npm/katex@0.12.0/dist/katex.min.js"),
		getScript("_auto-render.js", "https://cdn.jsdelivr.net/gh/Jwrede/Anki-KaTeX-Markdown/auto-render-cdn.js"),
		getScript("_markdown-it.min.js", "https://cdnjs.cloudflare.com/ajax/libs/markdown-it/12.0.4/markdown-it.min.js"),
		getScript("_markdown-it-mark.js","https://cdn.jsdelivr.net/gh/Jwrede/Anki-KaTeX-Markdown/_markdown-it-mark.js")
	];
	Promise.all(getResources).then(() => getScript("_mhchem.js", "https://cdn.jsdelivr.net/npm/katex@0.13.11/dist/contrib/mhchem.min.js")).then(render).catch(show);

	function getScript(path, altURL) {
		return new Promise((resolve, reject) => {
			let script = document.createElement("script");
			script.onload = resolve;
			script.onerror = function() {
				let script_online = document.createElement("script");
				script_online.onload = resolve;
				script_online.onerror = reject;
				script_online.src = altURL;
				document.head.appendChild(script_online);
			}
			script.src = path;
			document.head.appendChild(script);
		})
	}

	function getCSS(path, altURL) {
		return new Promise((resolve, reject) => {
			var css = document.createElement('link');
			css.setAttribute('rel', 'stylesheet');
			css.type = 'text/css';
			css.onload = resolve;
			css.onerror = function() {
				var css_online = document.createElement('link');
				css_online.setAttribute('rel', 'stylesheet');
				css_online.type = 'text/css';
				css_online.onload = resolve;
				css_online.onerror = reject;
				css_online.href = altURL;
				document.head.appendChild(css_online);
			}
			css.href = path;
			document.head.appendChild(css);
		});
	}

	function render() {
		//renderMath("front");
		//markdown("front");
		renderMath("back");
		markdown("back");
		show();
	}

	function show() {
		document.getElementById("front").style.visibility = "visible";
		document.getElementById("back").style.visibility = "visible";
	}


	function renderMath(ID) {
		let text = document.getElementById(ID).innerHTML;
		text = replaceInString(text);
		document.getElementById(ID).textContent = text;
		renderMathInElement(document.getElementById(ID), {
			delimiters:  [
				{left: "$$", right: "$$", display: true},
				{left: "$", right: "$", display: false}
			],
						throwOnError : false
		});
	}
	function markdown(ID) {
		let md = new markdownit({typographer: true, html:true, highlight: function (str, lang) {
							if (lang && hljs.getLanguage(lang)) {
								try {
									return hljs.highlight(str, { language: lang }).value;
								} catch (__) {}
							}

							return ''; // use external default escaping
						}}).use(markdownItMark);
		let text = replaceHTMLElementsInString(document.getElementById(ID).innerHTML);
		text = md.render(text);
		document.getElementById(ID).innerHTML = text.replace(/&lt;\/span&gt;/gi,"\\\\");
	}
	function replaceInString(str) {
		str = str.replace(/<[\/]?pre[^>]*>/gi, "");
		str = str.replace(/<br\s*[\/]?[^>]*>/gi, "\\n");
		str = str.replace(/<div[^>]*>/gi, "\\n");
		// Thanks Graham A!
		str = str.replace(/<[\/]?span[^>]*>/gi, "")
		str.replace(/<\/div[^>]*>/g, "\\n");
		return replaceHTMLElementsInString(str);
	}

	function replaceHTMLElementsInString(str) {
		str = str.replace(/&nbsp;/gi, " ");
		str = str.replace(/&tab;/gi, "	");
		str = str.replace(/&gt;/gi, ">");
		str = str.replace(/&lt;/gi, "<");
		return str.replace(/&amp;/gi, "&");
	}
</script>
"""

def parse_our_custom_md_file_to_cards( markdown_blob ):
	#cards = re.split( r'^##+/g' , markdown_blob )
	#print( cards[0] )
	#card_regions = markdown_blob.split( "##" )
	fronts = []
	backs = []
	in_progress = []
	for index , line in enumerate( markdown_blob ):
		if line.startswith( "## " ):
			fronts.append( line )
			if index != 0:
				backs.append( in_progress )
				in_progress = []
		else:
			in_progress.append( line )
	backs.append( in_progress )
	cards = []
	for index , front in enumerate( fronts ):
		# cards.append({
		# 	"front": front.split( "## " )[1].strip() ,
		# 	"back": markdown.markdown( "\n".join( backs[index] ) )
		# })
		cards.append([
			front.split( "## " )[1].strip() ,
			markdown.markdown( "\n".join( backs[index] ) )
		])
	# print( f"Fronts === {len(fronts)}" )
	# print( f"Backs === {len(backs)}" )
	# pprint( cards )
	return cards

time_zone = pytz.timezone( "US/Eastern" )
app = Sanic( __name__ )

# DEFAULT_CONFIG = utils.read_json( sys.argv[1] )

# app.static( "/host/static/js" , "./js" )
# app.static( "/host/static/css" , "./css" )

@app.route( "/" , methods=[ "GET" ] )
async def home( request: Request ):
	return sanic_html( f'''<!DOCTYPE html>
<html>
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<title>MD to Anki</title>
</head>
<body>
	<h1>Markdown to Anki Converter</h1>
	<form id="our-form" enctype="multipart/form-data" action="/convert" method="POST" onsubmit="on_submit();">
		<input type="file" id="powerpoint" name="file"><br><br>
		<input type="submit">
	</form>
	<script type="text/javascript">
		function on_submit() {{
			let form = document.getElementById( "our-form" );
			# let form_action = "/host/stage/2/" + hex_color;
			# form.action = form_action;
			form.submit();
		}}
	</script>
</body>
</html>''')

@app.route( "/convert" , methods=[ "POST" ] )
async def convert( request: Request ):
	try:
		# print( request.form )
		input_file = request.files.get( "file" )
		input_file_type = input_file.type
		input_file_name = input_file.name
		input_name_stem = ".".join( input_file_name.split( "." )[ 0 : -1 ] )
		input_file_data = input_file.body
		with tempfile.TemporaryDirectory() as temp_dir:
			temp_dir_posix = Path( temp_dir )
			with tempfile.NamedTemporaryFile( suffix=".md" , prefix=str( temp_dir_posix ) ) as tf:
				temp_file_path = temp_dir_posix.joinpath( tf.name )
				output_file_path = temp_dir_posix.joinpath( f"{input_name_stem}.apkg" )
				with open( str( temp_file_path ) , "wb"  ) as file:
					file.write( input_file_data )

				deck_name = input_name_stem
				md_file = read_text( str( temp_file_path ) )
				notes = parse_our_custom_md_file_to_cards( md_file )

				model_id = generate_model_id()
				deck_id = generate_model_id()
				# so real katex+md addon model number = 1636706072
				# https://ankiweb.net/shared/info/1087328706
				my_model = genanki.Model(
					model_id ,
					'Example',
					fields=[
						{ 'name': 'Front' } ,
						{ 'name': 'Back' } ,
					] ,
					templates=[
						{
							'name': 'Card 1',
							'qfmt': katex_markdown_front ,
							'afmt': katex_markdown_back ,
						} ,
					]
				)

				my_deck = genanki.Deck( deck_id , deck_name )

				for index , note in enumerate( notes ):
					x_note = genanki.Note(
						model=my_model ,
						fields=note
					)
					my_deck.add_note( x_note )

				my_package = genanki.Package( my_deck )
				# my_package.media_files = ['format.jpg']
				my_package.write_to_file( str( output_file_path ) )
				return await sanic_file(
					str( output_file_path ) ,
					# mime_type="application/zip" ,
					filename=output_file_path.name
				)
	except Exception as e:
		print( e )
		return sanic_json( dict( failed=str( e ) ) , status=200 )


if __name__ == "__main__":
	app.run( host="0.0.0.0" , port="9376" )
