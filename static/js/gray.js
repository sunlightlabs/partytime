/**
 * Gray theme for Highcharts JS
 * @author Torstein Hønsi
 */

Highcharts.theme = {
	colors: ["#93d2d1", "#7798BF", "#55BF3B", "#DF5353", "#aaeeee", "#ff0066", "#eeaaee",
		"#55BF3B", "#DF5353", "#7798BF", "#aaeeee"],
	chart: {
		backgroundColor: "#fbfaf7",
		borderWidth: 0,
		borderRadius: null,
		plotBackgroundColor: null,
		plotShadow: false,
		plotBorderWidth: 0,
	},
	title: {
		style: {
			color: '#000',
			font: '16px georgia, times new roman, san-serif',
			display: "none"
		}
	},
	subtitle: {
		style: {
			color: '#DDD',
			font: '12px georgia, times new roman, san-serif',
		}
	},
	xAxis: {
		gridLineWidth: 0,
		lineColor: '#d9d8d7',
		tickColor: '#d9d8d7',
		labels: {
			style: {
				color: '#999',
				fontWeight: 'bold'
			}
		},
		title: {
			style: {
				color: '#AAA',
				font: 'bold 12px georgia, times new roman, san-serif',
				display: "none",
			}
		}
	},
	yAxis: {
		alternateGridColor: null,
		minorTickInterval: null,
		gridLineColor: '#d9d8d7',
		lineWidth: 0,
		tickWidth: 0,
		labels: {
			style: {
				color: '#999',
				fontWeight: 'bold'
			}
		},
		title: {
			style: {
				color: '#AAA',
				font: 'bold 12px georgia, times new roman, san-serif',
				display: "none",
			}
		}
	},
	legend: {
		itemStyle: {
			color: '#CCC',
			display: 'none',
		},
		itemHoverStyle: {
			color: '#FFF',
		},
		itemHiddenStyle: {
			color: '#333',
		}
	},
	labels: {
		style: {
			color: '#CCC',
		}
	},
	tooltip: {
		backgroundColor: {
			linearGradient: [0, 0, 0, 50],
			stops: [
				[0, 'rgba(53, 48, 48, .8)'],
				[1, 'rgba(91, 86, 86, .8)']
			]
		},
		borderRadius: 0,
		borderWidth: 0,
		style: {
			color: '#FFF'
		}
	},
    credits : {
	    enabled : false
	},
	plotOptions: {
		line: {
		    animation: false,
			dataLabels: {
				color: '#CCC'
			},
			marker: {
				lineColor: '#333'
			}
		},
		spline: {
		    animation: false,		    
			marker: {
				lineColor: '#333'
			}
		},
		scatter: {
		    animation: false,		    
			marker: {
				lineColor: '#333'
			}
		},
		candlestick: {
		    animation: false,		    
			lineColor: 'white'
		}
	},

	toolbar: {
		itemStyle: {
			color: '#CCC',
		}
	},

	navigation: {
		buttonOptions: {
			backgroundColor: {
				linearGradient: [0, 0, 0, 20],
				stops: [
					[0.4, '#606060'],
					[0.6, '#333333']
				]
			},
			borderColor: '#000000',
			symbolStroke: '#C0C0C0',
			hoverSymbolStroke: '#FFFFFF',
		}
	},

	exporting: {
		buttons: {
			exportButton: {
				symbolFill: '#55BE3B'
			},
			printButton: {
				symbolFill: '#7797BE'
			}
		}
	},

	// scroll charts
	rangeSelector: {
		buttonTheme: {
			fill: {
				linearGradient: [0, 0, 0, 20],
				stops: [
					[0.4, '#888'],
					[0.6, '#555']
				]
			},
			stroke: '#000000',
			style: {
				color: '#CCC',
				fontWeight: 'bold'
			},
			states: {
				hover: {
					fill: {
						linearGradient: [0, 0, 0, 20],
						stops: [
							[0.4, '#BBB'],
							[0.6, '#888']
						]
					},
					stroke: '#000000',
					style: {
						color: 'white'
					}
				},
				select: {
					fill: {
						linearGradient: [0, 0, 0, 20],
						stops: [
							[0.1, '#000'],
							[0.3, '#333']
						]
					},
					stroke: '#000000',
					style: {
						color: 'yellow'
					}
				}
			}
		},
		inputStyle: {
			backgroundColor: '#333',
			color: 'silver'
		},
		labelStyle: {
			color: 'silver'
		}
	},

	navigator: {
		handles: {
			backgroundColor: '#666',
			borderColor: '#AAA'
		},
		outlineColor: '#CCC',
		maskFill: 'rgba(16, 16, 16, 0.5)',
		series: {
			color: '#7798BF',
			lineColor: '#A6C7ED'
		}
	},

	scrollbar: {
		barBackgroundColor: {
				linearGradient: [0, 0, 0, 20],
				stops: [
					[0.4, '#888'],
					[0.6, '#555']
				]
			},
		barBorderColor: '#CCC',
		buttonArrowColor: '#CCC',
		buttonBackgroundColor: {
				linearGradient: [0, 0, 0, 20],
				stops: [
					[0.4, '#888'],
					[0.6, '#555']
				]
			},
		buttonBorderColor: '#CCC',
		rifleColor: '#FFF',
		trackBackgroundColor: {
			linearGradient: [0, 0, 0, 10],
			stops: [
				[0, '#000'],
				[1, '#333']
			]
		},
		trackBorderColor: '#666'
	},

	// special colors for some of the demo examples
	legendBackgroundColor: 'rgba(48, 48, 48, 0.8)',
	legendBackgroundColorSolid: 'rgb(70, 70, 70)',
	dataLabelsColor: '#444',
	textColor: '#E0E0E0',
	maskColor: 'rgba(255,255,255,0.3)',
};

// Apply the theme
var highchartsOptions = Highcharts.setOptions(Highcharts.theme);
