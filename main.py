#!/usr/bin/env python3
import sys
import random
import genanki
import markdown
from pathlib import Path
from pprint import pprint

def read_text( file_path ):
	with open( file_path ) as f:
		return f.read().splitlines()
		#return f.read()

def generate_model_id():
	return random.randrange( 1 << 30 , 1 << 31 )

# https://github.com/kerrickstaley/genanki/blob/master/genanki/util.py
def generate_deck_id( *values ):
	BASE91_TABLE = [
	  'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's',
	  't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
	  'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3', '4',
	  '5', '6', '7', '8', '9', '!', '#', '$', '%', '&', '(', ')', '*', '+', ',', '-', '.', '/', ':',
	  ';', '<', '=', '>', '?', '@', '[', ']', '^', '_', '`', '{', '|', '}', '~']

	hash_string = '__'.join( str( val ) for val in values )
	# get the first 8 bytes of the SHA256 of hash_string as an int
	m = hashlib.sha256()
	m.update( hash_string.encode( 'utf-8' ) )
	hash_bytes = m.digest()[ :8 ]
	hash_int = 0
	for b in hash_bytes:
		hash_int <<= 8
		hash_int += b

	# convert to the weird base91 format that Anki uses
	rv_reversed = []
	while hash_int > 0:
		rv_reversed.append( BASE91_TABLE[ hash_int % len( BASE91_TABLE ) ] )
		hash_int //= len( BASE91_TABLE )

	return ''.join( reversed( rv_reversed ) )

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

katex_markdown_back = """

<div id="back"><pre>{{Back}}</pre></div>

<script>
	var getResources = [
		getCSS("_katex.css", "https://cdn.jsdelivr.net/npm/katex@0.12.0/dist/katex.min.css"),
		getCSS("_highlight.css", "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.0.1/styles/default.min.css"),
		getScript("_highlight.js", "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.0.1/highlight.min.js"),
		getScript("_katex.min.js", "https://39363.org/CDN/katex/katex.min.js"),
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

# https://ankiweb.net/shared/info/1087328706
def create_katex_markdown_deck( deck_title , notes ):
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

	my_deck = genanki.Deck( deck_id , deck_title )

	for index , note in enumerate( notes ):
		x_note = genanki.Note(
			model=my_model ,
			fields=note
		)
		my_deck.add_note( x_note )

	my_package = genanki.Package( my_deck )
	# my_package.media_files = ['format.jpg']
	my_package.write_to_file( f"{deck_title}.apkg" )


if __name__ == "__main__":
	input_file_path = Path( sys.argv[ 1 ] )
	deck_name = input_file_path.stem
	md_file = read_text( sys.argv[ 1 ] )
	cards = parse_our_custom_md_file_to_cards( md_file )
	pprint( cards )
	create_katex_markdown_deck( deck_name , cards )
