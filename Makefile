pdf_all: scores
	python lilypond.py -a ;\

pdf_score: scores
	python lilypond.py -s ;\

scores:
	python lilytool.py -l ;\

clean:
	python lilytool.py -c ;\
	find . -name "*~" ;\

create:
	python lilytool.py --create y ;\
