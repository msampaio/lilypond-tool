default: create_without_overwrite scores pdf_all

pdf_all: scores
	python lilytool.py -a ;\

pdf_score: scores
	python lilytool.py -s ;\

scores:
	python lilytool.py -l ;\

all_clean: clean
	python lilytool.py --all_clean ;\

clean:
	python lilytool.py -c ;\
	find . -name "*~" ;\

create:
	python lilytool.py --create y ;\

create_without_overwrite:
	python lilytool.py --create n ;\
