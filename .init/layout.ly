\layout {
  \context { \Score
             \override MetronomeMark.extra-offset = #'(-9 . 0)
             \override MetronomeMark.padding = #'3
           }
  \context { \Staff
             \override TimeSignature.style = #'numbered
           }
  \context { \Voice
             \override Glissando.thickness = #3
             \override Glissando.gap = #0.1
           }
  \context { \Staff
             \consists "Horizontal_bracket_engraver"
           }
}
